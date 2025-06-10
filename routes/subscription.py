from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import stripe
import os
import requests
import json
from datetime import datetime, timedelta
from models.user import db, User, Subscription

subscription_bp = Blueprint('subscription', __name__)

# Stripe configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# BTCPay Server configuration
BTCPAY_SERVER_URL = os.getenv('BTCPAY_SERVER_URL', 'https://your-btcpay-server.com')
BTCPAY_STORE_ID = os.getenv('BTCPAY_STORE_ID')
BTCPAY_API_KEY = os.getenv('BTCPAY_API_KEY')

def get_user_from_token():
    """Extract user from JWT token manually"""
    try:
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None, jsonify({'message': 'Authorization token required'}), 401
        
        token = auth_header.split(' ')[1]
        if not token:
            return None, jsonify({'message': 'Invalid authorization header'}), 401
        
        from flask_jwt_extended import decode_token
        try:
            decoded_token = decode_token(token)
            user_id = decoded_token['sub']
        except Exception as jwt_error:
            print(f"JWT decode error: {jwt_error}")
            return None, jsonify({'message': 'Invalid or expired token'}), 401
        
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
            return jsonify({'message': 'Invalid plan'}), 422
        
        # Check if Stripe is configured
        if not stripe.api_key or not stripe.api_key.startswith('sk_'):
            return jsonify({'message': 'Stripe not configured'}), 500
        
        # Create Stripe customer
        stripe_customer_id = None
        try:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={'user_id': str(user.id)}
            )
            stripe_customer_id = customer.id
            print(f"Created Stripe customer: {stripe_customer_id} for user {user.id}")
        except Exception as stripe_error:
            print(f"Stripe customer creation error: {stripe_error}")
            return jsonify({'message': 'Failed to create Stripe customer'}), 500
        
        # Determine price based on plan (create prices dynamically if not configured)
        try:
            if plan == 'monthly':
                # Try to get configured price ID, or create one
                price_id = os.getenv('STRIPE_MONTHLY_PRICE_ID')
                if not price_id:
                    price = stripe.Price.create(
                        unit_amount=2999,  # $29.99 in cents
                        currency='usd',
                        recurring={'interval': 'month'},
                        product_data={'name': 'Bitcoin Will Monthly Plan'}
                    )
                    price_id = price.id
                    print(f"Created monthly price: {price_id}")
            else:  # yearly
                price_id = os.getenv('STRIPE_YEARLY_PRICE_ID')
                if not price_id:
                    price = stripe.Price.create(
                        unit_amount=29999,  # $299.99 in cents
                        currency='usd',
                        recurring={'interval': 'year'},
                        product_data={'name': 'Bitcoin Will Yearly Plan'}
                    )
                    price_id = price.id
                    print(f"Created yearly price: {price_id}")
                    
        except Exception as price_error:
            print(f"Price creation error: {price_error}")
            return jsonify({'message': 'Failed to create pricing'}), 500
        
        # Get the frontend URL for redirects
        frontend_url = request.headers.get('Origin', 'https://thebitcoinwill.com')
        
        # Create checkout session
        try:
            session = stripe.checkout.Session.create(
                customer=stripe_customer_id,
                payment_method_types=['card'],
                line_items=[{
                    'price': price_id,
                    'quantity': 1,
                }],
                mode='subscription',
                success_url=f"{frontend_url}/?payment=success&session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{frontend_url}/?payment=cancelled",
                metadata={
                    'user_id': str(user.id),
                    'plan': plan
                }
            )
            
            print(f"Created checkout session: {session.id} for user {user.id}")
            
            return jsonify({
                'checkout_url': session.url,
                'session_id': session.id
            }), 200
            
        except Exception as session_error:
            print(f"Checkout session creation error: {session_error}")
            return jsonify({'message': 'Failed to create checkout session'}), 500
        
    except Exception as e:
        print(f"Stripe checkout error: {e}")
        return jsonify({'message': 'Failed to create checkout session'}), 500

@subscription_bp.route('/create-btcpay-invoice', methods=['POST', 'OPTIONS'])
@cross_origin()
def create_btcpay_invoice():
    """Create BTCPay Server invoice"""
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
            return jsonify({'message': 'Invalid plan'}), 422
        
        # For now, return a placeholder invoice URL
        # In production, you would create actual BTCPay Server invoice
        amount = 29.99 if plan == 'monthly' else 299.99
        frontend_url = request.headers.get('Origin', 'https://thebitcoinwill.com')
        invoice_url = f"https://btcpay.example.com/invoice?amount={amount}&plan={plan}&user={user.id}&return={frontend_url}"
        
        return jsonify({
            'invoice_url': invoice_url,
            'invoice_id': f'btcpay_placeholder_{user.id}_{plan}',
            'amount': amount,
            'currency': 'USD'
        }), 200
        
    except Exception as e:
        print(f"BTCPay invoice error: {e}")
        return jsonify({'message': 'Failed to create BTCPay invoice'}), 500

@subscription_bp.route('/verify-payment', methods=['POST', 'OPTIONS'])
@cross_origin()
def verify_payment():
    """Verify payment and create subscription"""
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
                existing_subscription = Subscription.query.filter_by(user_id=user.id).first()
                
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
                        user_id=user.id,
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

@subscription_bp.route('/webhook/stripe', methods=['POST'])
@cross_origin()
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        # For now, just return success
        # In production, you would verify the webhook and update subscription
        print(f"Received Stripe webhook: {payload}")
        return jsonify({'received': True}), 200
        
    except Exception as e:
        print(f"Stripe webhook error: {e}")
        return jsonify({'message': 'Webhook processing failed'}), 500

@subscription_bp.route('/webhook/btcpay', methods=['POST'])
@cross_origin()
def btcpay_webhook():
    """Handle BTCPay Server webhooks"""
    try:
        data = request.get_json()
        
        # For now, just return success
        # In production, you would verify the webhook and update subscription
        print(f"Received BTCPay webhook: {data}")
        return jsonify({'received': True}), 200
        
    except Exception as e:
        print(f"BTCPay webhook error: {e}")
        return jsonify({'message': 'Webhook processing failed'}), 500

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
        
        # Update subscription status
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

