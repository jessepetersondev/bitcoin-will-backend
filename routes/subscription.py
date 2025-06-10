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

@subscription_bp.route('/create-checkout-session', methods=['POST', 'OPTIONS'])
@jwt_required(optional=True)
@cross_origin()
def create_stripe_checkout_session():
    """Create Stripe checkout session"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({'message': 'Authentication required'}), 401
            
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        plan = data.get('plan')
        
        if plan not in ['monthly', 'yearly']:
            return jsonify({'message': 'Invalid plan'}), 400
        
        # Get price ID from environment
        price_id = os.getenv('STRIPE_MONTHLY_PRICE_ID') if plan == 'monthly' else os.getenv('STRIPE_YEARLY_PRICE_ID')
        
        if not price_id:
            return jsonify({'message': 'Price ID not configured'}), 500
        
        # Create or get Stripe customer
        if not user.stripe_customer_id:
            customer = stripe.Customer.create(
                email=user.email,
                metadata={'user_id': str(user.id)}
            )
            user.stripe_customer_id = customer.id
            db.session.commit()
        
        # Create checkout session
        session = stripe.checkout.Session.create(
            customer=user.stripe_customer_id,
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

@subscription_bp.route('/status', methods=['GET'])
@jwt_required(optional=True)
@cross_origin()
def get_subscription_status():
    """Get user's subscription status"""
    try:
        user_id = get_jwt_identity()
        if not user_id:
            return jsonify({
                'active': False,
                'plan': None,
                'status': 'none',
                'next_billing_date': None
            }), 200
            
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        
        if not subscription:
            return jsonify({
                'active': False,
                'plan': None,
                'status': 'none',
                'next_billing_date': None
            }), 200
        
        return jsonify({
            'active': subscription.status == 'active',
            'plan': subscription.plan,
            'status': subscription.status,
            'payment_method': subscription.payment_method,
            'next_billing_date': subscription.current_period_end.isoformat() if subscription.current_period_end else None
        }), 200
        
    except Exception as e:
        print(f"Subscription status error: {e}")
        return jsonify({'message': 'Failed to get subscription status'}), 500

