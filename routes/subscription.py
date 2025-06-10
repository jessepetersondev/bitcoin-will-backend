from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import stripe
import os
import json
from datetime import datetime, timedelta
from models.user import db, User, Subscription

subscription_bp = Blueprint('subscription', __name__)

# Stripe configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

def get_user_from_token():
    """Extract user from JWT token - FIXED VERSION"""
    try:
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return None, jsonify({'message': 'Authorization header missing'}), 401
        
        if not auth_header.startswith('Bearer '):
            return None, jsonify({'message': 'Invalid authorization header format'}), 401
        
        token = auth_header.split(' ')[1]
        
        if not token:
            return None, jsonify({'message': 'Token missing from authorization header'}), 401
        
        # Import JWT functions
        try:
            import jwt
            JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'fallback-secret-key')
            
            # Decode the token manually
            decoded_token = jwt.decode(token, JWT_SECRET_KEY, algorithms=['HS256'])
            user_id_str = decoded_token.get('sub')
            
            if not user_id_str:
                return None, jsonify({'message': 'Invalid token payload'}), 401
            
            # Convert string back to integer
            user_id = int(user_id_str)
                
        except jwt.ExpiredSignatureError:
            return None, jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError as e:
            print(f"JWT decode error: {e}")
            return None, jsonify({'message': 'Invalid token'}), 401
        except ValueError:
            return None, jsonify({'message': 'Invalid user ID in token'}), 401
        except Exception as jwt_error:
            print(f"JWT processing error: {jwt_error}")
            return None, jsonify({'message': 'Token validation failed'}), 401
        
        user = User.query.get(user_id)
        
        if not user:
            return None, jsonify({'message': 'User not found'}), 404
            
        return user, None, None
        
    except Exception as e:
        print(f"Token validation error: {e}")
        return None, jsonify({'message': 'Authentication failed'}), 401

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
@cross_origin()
def create_stripe_checkout_session():
    """Create Stripe checkout session"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
            
        plan = data.get('plan')
        
        if plan not in ['monthly', 'yearly']:
            return jsonify({'message': 'Invalid plan. Must be "monthly" or "yearly"'}), 422
        
        # Check if Stripe is configured
        if not stripe.api_key:
            return jsonify({'message': 'Stripe not configured - missing STRIPE_SECRET_KEY'}), 500
            
        if not stripe.api_key.startswith('sk_'):
            return jsonify({'message': 'Invalid Stripe secret key format'}), 500
        
        print(f"Creating checkout session for user {user.id}, plan: {plan}")
        
        # Create price dynamically (like working app.py)
        try:
            if plan == 'monthly':
                price = stripe.Price.create(
                    unit_amount=2999,  # $29.99 in cents
                    currency='usd',
                    recurring={'interval': 'month'},
                    product_data={'name': 'Bitcoin Will Monthly Plan'}
                )
                price_id = price.id
                print(f"Created monthly price: {price_id}")
            else:  # yearly
                price = stripe.Price.create(
                    unit_amount=29999,  # $299.99 in cents
                    currency='usd',
                    recurring={'interval': 'year'},
                    product_data={'name': 'Bitcoin Will Yearly Plan'}
                )
                price_id = price.id
                print(f"Created yearly price: {price_id}")
                
        except Exception as price_error:
            print(f"Failed to create price: {price_error}")
            return jsonify({'message': f'Failed to create pricing: {str(price_error)}'}), 500
        
        # Get the frontend URL for redirects
        frontend_url = request.headers.get('Origin', 'https://thebitcoinwill.com')
        print(f"Frontend URL: {frontend_url}")
        
        # Create checkout session
        try:
            print(f"Creating Stripe checkout session with price_id: {price_id}")
            
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
            
            print(f"Successfully created checkout session: {session.id}")
            
            return jsonify({
                'checkout_url': session.url,
                'session_id': session.id
            }), 200
            
        except Exception as session_error:
            print(f"Checkout session creation error: {session_error}")
            return jsonify({'message': f'Failed to create checkout session: {str(session_error)}'}), 500
        
    except Exception as e:
        print(f"General checkout error: {e}")
        return jsonify({'message': f'Checkout failed: {str(e)}'}), 500

@subscription_bp.route('/verify-payment', methods=['POST', 'OPTIONS'])
@cross_origin()
def verify_payment():
    """Verify payment and create subscription - FIXED VERSION"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No data provided'}), 422
            
        session_id = data.get('session_id')
        if not session_id:
            return jsonify({'message': 'Session ID required'}), 422
        
        print(f"Verifying payment for session: {session_id}")
        
        # Retrieve the session from Stripe
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            print(f"Retrieved session: {session.payment_status}")
            
            if session.payment_status == 'paid':
                # Get subscription details
                subscription_id = session.subscription
                print(f"Subscription ID: {subscription_id}")
                
                if subscription_id:
                    stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                    print(f"Retrieved subscription: {stripe_subscription.status}")
                    
                    # Determine plan type from metadata
                    plan_type = session.metadata.get('plan', 'monthly')
                    amount = 29.99 if plan_type == 'monthly' else 299.99
                    
                    print(f"Plan type: {plan_type}, Amount: {amount}")
                    
                    # Create or update subscription in database
                    existing_subscription = Subscription.query.filter_by(user_id=user.id).first()
                    
                    # FIXED: Safely access current_period_start and current_period_end
                    try:
                        period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
                        period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                    except (AttributeError, TypeError) as period_error:
                        print(f"Period access error: {period_error}")
                        # Use current time as fallback
                        period_start = datetime.utcnow()
                        period_end = datetime.utcnow() + timedelta(days=30 if plan_type == 'monthly' else 365)
                    
                    if existing_subscription:
                        # Update existing subscription
                        existing_subscription.plan_type = plan_type
                        existing_subscription.status = 'active'
                        existing_subscription.stripe_subscription_id = subscription_id
                        existing_subscription.payment_method = 'stripe'
                        existing_subscription.amount = amount
                        existing_subscription.current_period_start = period_start
                        existing_subscription.current_period_end = period_end
                        existing_subscription.updated_at = datetime.utcnow()
                        print("Updated existing subscription")
                    else:
                        # Create new subscription
                        new_subscription = Subscription(
                            user_id=user.id,
                            plan_type=plan_type,
                            status='active',
                            stripe_subscription_id=subscription_id,
                            payment_method='stripe',
                            amount=amount,
                            currency='USD',
                            current_period_start=period_start,
                            current_period_end=period_end
                        )
                        db.session.add(new_subscription)
                        print("Created new subscription")
                    
                    db.session.commit()
                    print("Subscription saved to database")
                    
                    return jsonify({
                        'message': 'Payment verified and subscription activated',
                        'subscription': {
                            'plan_type': plan_type,
                            'status': 'active',
                            'amount': amount
                        }
                    }), 200
                else:
                    print("No subscription ID found in session")
                    return jsonify({'message': 'No subscription found in payment session'}), 400
            else:
                print(f"Payment not completed: {session.payment_status}")
                return jsonify({'message': 'Payment not completed'}), 400
                
        except Exception as stripe_error:
            print(f"Stripe verification error: {stripe_error}")
            return jsonify({'message': 'Failed to verify payment'}), 500
        
    except Exception as e:
        db.session.rollback()
        print(f"Payment verification error: {e}")
        return jsonify({'message': 'Failed to verify payment'}), 500

@subscription_bp.route('/status', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_subscription_status():
    """Get user's subscription status"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        # Get active subscription
        subscription = Subscription.query.filter_by(
            user_id=user.id, 
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

# FIXED: Correct webhook URL path
@subscription_bp.route('/webhook/stripe', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin()
def stripe_webhook():
    """Handle Stripe webhooks - FIXED URL PATH"""
    if request.method in ('GET', 'OPTIONS'):
        return jsonify({'status': 'ok'}), 200

    try:
        payload = request.get_data(as_text=True)
        sig_header = request.headers.get('Stripe-Signature')
        
        print(f"Webhook received: {len(payload)} bytes")
        
        # Parse JSON directly (webhook secret optional)
        event = json.loads(payload)
        print(f"Webhook processed: {event['type']}")
        
        event_type = event['type']
        
        # Handle checkout session completed
        if event_type in ('checkout.session.completed', 'checkout.session.async_payment_succeeded'):
            session = event['data']['object']
            user_id = session['metadata'].get('user_id')
            plan = session['metadata'].get('plan')
            
            print(f"Checkout completed for user {user_id}, plan {plan}")
            
            if user_id:
                try:
                    subscription_id = session.get('subscription')
                    if subscription_id:
                        stripe_subscription = stripe.Subscription.retrieve(subscription_id)
                        
                        # Create or update subscription
                        existing_subscription = Subscription.query.filter_by(user_id=int(user_id)).first()
                        amount = 29.99 if plan == 'monthly' else 299.99
                        
                        # FIXED: Safely access period data
                        try:
                            period_start = datetime.fromtimestamp(stripe_subscription.current_period_start)
                            period_end = datetime.fromtimestamp(stripe_subscription.current_period_end)
                        except (AttributeError, TypeError):
                            period_start = datetime.utcnow()
                            period_end = datetime.utcnow() + timedelta(days=30 if plan == 'monthly' else 365)
                        
                        if existing_subscription:
                            existing_subscription.status = 'active'
                            existing_subscription.stripe_subscription_id = subscription_id
                            existing_subscription.plan_type = plan
                            existing_subscription.amount = amount
                            existing_subscription.current_period_start = period_start
                            existing_subscription.current_period_end = period_end
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
                                current_period_start=period_start,
                                current_period_end=period_end
                            )
                            db.session.add(new_subscription)
                        
                        db.session.commit()
                        print(f"Subscription activated for user {user_id}")
                        
                except Exception as db_error:
                    print(f"Database error in webhook: {db_error}")
                    db.session.rollback()
        
        return jsonify({'received': True}), 200
        
    except Exception as e:
        print(f"Webhook processing error: {e}")
        return jsonify({'error': 'Webhook processing failed'}), 500

@subscription_bp.route('/cancel', methods=['POST', 'OPTIONS'])
@cross_origin()
def cancel_subscription():
    """Cancel user's subscription"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        user, error_response, status_code = get_user_from_token()
        if not user:
            return error_response, status_code
        
        subscription = Subscription.query.filter_by(
            user_id=user.id, 
            status='active'
        ).first()
        
        if not subscription:
            return jsonify({'message': 'No active subscription found'}), 404
        
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

