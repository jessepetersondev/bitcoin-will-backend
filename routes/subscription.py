from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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
@jwt_required()
@cross_origin()
def create_stripe_checkout_session():
    """Create Stripe checkout session"""
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
        
        # Get price ID from environment
        price_id = os.getenv('STRIPE_MONTHLY_PRICE_ID') if plan == 'monthly' else os.getenv('STRIPE_YEARLY_PRICE_ID')
        
        if not price_id:
            return jsonify({'message': 'Price ID not configured'}), 500
        
        # Create Stripe customer if needed
        stripe_customer_id = None
        try:
            if stripe.api_key and stripe.api_key.startswith('sk_'):
                # Create customer for this session
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={'user_id': str(user.id)}
                )
                stripe_customer_id = customer.id
        except Exception as stripe_error:
            print(f"Stripe customer creation error: {stripe_error}")
            return jsonify({'message': 'Failed to create Stripe customer'}), 500
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            mode='subscription',
            success_url=request.host_url + 'success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=request.host_url + 'cancel',
            metadata={
                'user_id': str(user.id),
                'plan': plan
            }
        )
        
        return jsonify({'checkout_url': session.url}), 200
        
    except Exception as e:
        print(f"Stripe checkout error: {e}")
        return jsonify({'message': 'Failed to create checkout session'}), 500

@subscription_bp.route('/create-btcpay-invoice', methods=['POST', 'OPTIONS'])
@jwt_required()
@cross_origin()
def create_btcpay_invoice():
    """Create BTCPay Server invoice"""
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
        
        # For now, return a placeholder invoice URL
        # In production, you would create actual BTCPay Server invoice
        amount = 29.99 if plan == 'monthly' else 299.99
        invoice_url = f"https://btcpay.example.com/invoice?amount={amount}&plan={plan}&user={user_id}"
        
        return jsonify({
            'invoice_url': invoice_url,
            'invoice_id': f'btcpay_placeholder_{user_id}_{plan}',
            'amount': amount,
            'currency': 'USD'
        }), 200
        
    except Exception as e:
        print(f"BTCPay invoice error: {e}")
        return jsonify({'message': 'Failed to create BTCPay invoice'}), 500

@subscription_bp.route('/status', methods=['GET'])
@jwt_required()
@cross_origin()
def get_subscription_status():
    """Get user's subscription status"""
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

@subscription_bp.route('/webhook/stripe', methods=['POST'])
@cross_origin()
def stripe_webhook():
    """Handle Stripe webhooks"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        # For now, just return success
        # In production, you would verify the webhook and update subscription
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
        return jsonify({'received': True}), 200
        
    except Exception as e:
        print(f"BTCPay webhook error: {e}")
        return jsonify({'message': 'Webhook processing failed'}), 500

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

