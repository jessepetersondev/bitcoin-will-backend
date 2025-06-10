from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from flask_cors import cross_origin
import stripe
import os
import json
from datetime import datetime, timedelta
from models.user import db, User, Subscription

subscription_bp = Blueprint('subscription', __name__)

# Stripe configuration - using the working pattern
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Use single price IDs like the working app
MONTHLY_PRICE_ID = os.getenv('STRIPE_MONTHLY_PRICE_ID', '')  # Replace with actual price ID
YEARLY_PRICE_ID = os.getenv('STRIPE_YEARLY_PRICE_ID', '')   # Replace with actual price ID

@subscription_bp.route('/plans', methods=['GET'])
@cross_origin()
def get_subscription_plans():
    """Get available subscription plans"""
    try:
        plans = [
            {
                'id': 'monthly',
                'name': 'Monthly Plan',
                'price': 29.99,
                'currency': 'USD',
                'interval': 'month',
                'stripe_price_id': MONTHLY_PRICE_ID,
                'features': [
                    'Unlimited Bitcoin wills',
                    'Secure document generation',
                    'Beneficiary management',
                    'Legal template library',
                    'Email support'
                ]
            },
            {
                'id': 'yearly',
                'name': 'Yearly Plan',
                'price': 299.99,
                'currency': 'USD',
                'interval': 'year',
                'stripe_price_id': YEARLY_PRICE_ID,
                'features': [
                    'Unlimited Bitcoin wills',
                    'Secure document generation',
                    'Beneficiary management',
                    'Legal template library',
                    'Priority support'
                ],
                'savings': '17% savings'
            }
        ]
        
        return jsonify({'plans': plans}), 200
        
    except Exception as e:
        print(f"Get plans error: {e}")
        return jsonify({'message': 'Failed to get subscription plans'}), 500

@subscription_bp.route('/create-checkout-session', methods=['POST', 'OPTIONS'])
@jwt_required()
@cross_origin()
def create_stripe_checkout_session():
    """Create Stripe checkout session - using working pattern"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
            
        plan = data.get('plan')
        
        if plan not in ['monthly', 'yearly']:
            return jsonify({'message': 'Invalid plan'}), 422
        
        # Check if Stripe is configured
        if not stripe.api_key or not stripe.api_key.startswith('sk_'):
            return jsonify({'message': 'Stripe not configured'}), 500
        
        # Use the working pattern - simple price ID selection
        price_id = MONTHLY_PRICE_ID if plan == 'monthly' else YEARLY_PRICE_ID
        
        if not price_id or price_id.startswith('price_123'):  # Check for placeholder
            return jsonify({'message': 'Stripe price IDs not configured properly'}), 500
        
        # Get the frontend URL for redirects
        frontend_url = request.headers.get('Origin', 'https://thebitcoinwill.com')
        
        # Create checkout session using the working pattern
        try:
            session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1
                }],
                mode='subscription',
                success_url=f"{frontend_url}/?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{frontend_url}/?payment=cancelled",
                metadata={
                    'user_id': str(user.id),
                    'user_email': user.email,
                    'plan': plan
                },
                subscription_data={
                    'metadata': {
                        'user_id': str(user.id),
                        'user_email': user.email,
                        'plan': plan
                    }
                }
            )
            
            print(f"Created checkout session: {session.id} for user {user.id}")
            
            return jsonify({
                'checkout_url': session.url,
                'session_id': session.id
            }), 200
            
        except Exception as session_error:
            print(f"Checkout session creation error: {session_error}")
            return jsonify({'message': f'Failed to create checkout session: {str(session_error)}'}), 500
        
    except Exception as e:
        print(f"Stripe checkout error: {e}")
        return jsonify({'message': 'Failed to create checkout session'}), 500

@subscription_bp.route('/verify-payment', methods=['POST', 'OPTIONS'])
@jwt_required()
@cross_origin()
def verify_payment():
    """Verify payment and create subscription"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
            
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({'message': 'Session ID required'}), 422
        
        # Retrieve the session from Stripe
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            
            if session.payment_status == 'paid':
                # Get subscription details
                subscription_id = session.subscription
                stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                
                # Determine plan type from metadata
                plan_type = session.metadata.get('plan', 'monthly')
                amount = 29.99 if plan_type == 'monthly' else 299.99
                
                # Create or update subscription in database
                existing_subscription = Subscription.query.filter_by(user_id=user_id).first()
                
                if existing_subscription:
                    # Update existing subscription
                    existing_subscription.plan_type = plan_type
                    existing_subscription.status = 'active'
                    existing_subscription.stripe_subscription_id = subscription_id
                    existing_subscription.payment_method = 'stripe'
                    existing_subscription.amount = amount
                    existing_subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
                    existing_subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                    existing_subscription.updated_at = datetime.utcnow()
                else:
                    # Create new subscription
                    new_subscription = Subscription(
                        user_id=user_id,
                        plan_type=plan_type,
                        status='active',
                        stripe_subscription_id=subscription_id,
                        payment_method='stripe',
                        amount=amount,
                        currency='USD',
                        current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                        current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end)
                    )
                    db.session.add(new_subscription)
                
                db.session.commit()
                
                return jsonify({
                    'message': 'Payment verified and subscription activated',
                    'subscription': {
                        'plan_type': plan_type,
                        'status': 'active',
                        'amount': amount
                    }
                }), 200
            else:
                return jsonify({'message': 'Payment not completed'}), 400
                
        except Exception as stripe_error:
            print(f"Stripe verification error: {stripe_error}")
            return jsonify({'message': 'Failed to verify payment'}), 500
        
    except Exception as e:
        db.session.rollback()
        print(f"Payment verification error: {e}")
        return jsonify({'message': 'Failed to verify payment'}), 500

@subscription_bp.route('/status', methods=['GET', 'OPTIONS'])
@jwt_required()
@cross_origin()
def get_subscription_status():
    """Get user's subscription status"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        # Get active subscription
        subscription = Subscription.query.filter_by(
            user_id=user_id, 
            status='active'
        ).first()
        
        if subscription:
            return jsonify({
                'active': True,
                'subscription': subscription.to_dict()
            }), 200
        else:
            return jsonify({
                'active': False,
                'subscription': None
            }), 200
            
    except Exception as e:
        print(f"Subscription status error: {e}")
        return jsonify({'message': 'Failed to get subscription status'}), 500

@subscription_bp.route('/webhook/stripe', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin()
def stripe_webhook():
    """Handle Stripe webhooks - using working pattern"""
    if request.method in ('GET', 'OPTIONS'):
        return jsonify({'status': 'ok'}), 200

    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        
        print(f"Webhook received: {len(payload)} bytes")
        
        # Verify webhook signature if secret is configured
        if WEBHOOK_SECRET:
            try:
                event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
                print(f"Webhook signature verified: {event['type']}")
            except Exception as e:
                print(f"Webhook signature verification failed: {e}")
                return jsonify({'error': 'Invalid signature'}), 400
        else:
            # If no webhook secret, parse JSON directly (less secure)
            event = json.loads(payload)
            print(f"Webhook processed without signature verification: {event['type']}")
        
        event_type = event['type']
        print(f"Processing webhook event: {event_type}")
        
        # Handle checkout session completed
        if event_type in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
            session = event['data']['object']
            user_id = session['metadata'].get('user_id')
            user_email = session['metadata'].get('user_email')
            plan = session['metadata'].get('plan')
            
            print(f"Checkout completed for user {user_id}, email {user_email}, plan {plan}")
            
            if user_id:
                # Update subscription in database
                try:
                    subscription_id = session.get('subscription')
                    if subscription_id:
                        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                        
                        # Create or update subscription
                        existing_subscription = Subscription.query.filter_by(user_id=int(user_id)).first()
                        amount = 29.99 if plan == 'monthly' else 299.99
                        
                        if existing_subscription:
                            existing_subscription.status = 'active'
                            existing_subscription.stripe_subscription_id = subscription_id
                            existing_subscription.plan_type = plan
                            existing_subscription.amount = amount
                            existing_subscription.current_period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
                            existing_subscription.current_period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                            existing_subscription.updated_at = datetime.utcnow()
                        else:
                            new_subscription = Subscription(
                                user_id=int(user_id),
                                plan_type=plan,
                                status='active',
                                stripe_subscription_id=subscription_id,
                                payment_method='stripe',
                                amount=amount,
                                currency='USD',
                                current_period_start=datetime.fromtimestamp(stripe_subscription.current_period_start),
                                current_period_end=datetime.fromtimestamp(stripe_subscription.current_period_end)
                            )
                            db.session.add(new_subscription)
                        
                        db.session.commit()
                        print(f"Subscription activated for user {user_id}")
                        
                except Exception as db_error:
                    print(f"Database error in webhook: {db_error}")
                    db.session.rollback()
        
        # Handle subscription updates
        elif event_type == 'customer.subscription.updated':
            subscription = event['data']['object']
            status = subscription.get('status')
            user_id = subscription.get('metadata', {}).get('user_id')
            
            print(f"Subscription updated: user {user_id}, status {status}")
            
            if user_id:
                db_subscription = Subscription.query.filter_by(
                    user_id=int(user_id),
                    stripe_subscription_id=subscription['id']
                ).first()
                
                if db_subscription:
                    db_subscription.status = 'active' if status == 'active' else 'cancelled'
                    db_subscription.updated_at = datetime.utcnow()
                    db.session.commit()
                    print(f"Updated subscription status to {db_subscription.status}")
        
        # Handle subscription deletion
        elif event_type == 'customer.subscription.deleted':
            subscription = event['data']['object']
            user_id = subscription.get('metadata', {}).get('user_id')
            
            print(f"Subscription deleted for user {user_id}")
            
            if user_id:
                db_subscription = Subscription.query.filter_by(
                    user_id=int(user_id),
                    stripe_subscription_id=subscription['id']
                ).first()
                
                if db_subscription:
                    db_subscription.status = 'cancelled'
                    db_subscription.updated_at = datetime.utcnow()
                    db.session.commit()
                    print(f"Marked subscription as cancelled")
        
        return jsonify({'received': True}), 200
        
    except Exception as e:
        print(f"Webhook processing error: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@subscription_bp.route('/cancel', methods=['POST', 'OPTIONS'])
@jwt_required()
@cross_origin()
def cancel_subscription():
    """Cancel user's subscription"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user_id = get_jwt_identity()
        subscription = Subscription.query.filter_by(
            user_id=user_id, 
            status='active'
        ).first()
        
        if not subscription:
            return jsonify({'message': 'No active subscription found'}), 404
        
        # Cancel in Stripe if we have the subscription ID
        if subscription.stripe_subscription_id:
            try:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                print(f"Cancelled Stripe subscription {subscription.stripe_subscription_id}")
            except Exception as stripe_error:
                print(f"Error cancelling Stripe subscription: {stripe_error}")
        
        # Update subscription status in database
        subscription.status = 'cancelled'
        subscription.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription cancelled successfully',
            'subscription': subscription.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        print(f"Cancel subscription error: {e}")
        return jsonify({'message': 'Failed to cancel subscription'}), 500

