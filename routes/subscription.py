from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
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

@subscription_bp.route('/create-checkout-session', methods=['POST'])
@jwt_required()
def create_stripe_checkout_session():
    """Create Stripe checkout session"""
    try:
        user_id = get_jwt_identity()
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
        return jsonify({'message': str(e)}), 500

@subscription_bp.route('/create-btcpay-invoice', methods=['POST'])
@jwt_required()
def create_btcpay_invoice():
    """Create BTCPay Server invoice"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'message': 'User not found'}), 404
        
        data = request.get_json()
        plan = data.get('plan')
        
        if plan not in ['monthly', 'yearly']:
            return jsonify({'message': 'Invalid plan'}), 400
        
        # Set price based on plan
        amount = 29.99 if plan == 'monthly' else 299.99
        
        # Create BTCPay Server invoice
        invoice_data = {
            'amount': amount,
            'currency': 'USD',
            'orderId': f'sub_{user.id}_{plan}_{int(datetime.now().timestamp())}',
            'buyerEmail': user.email,
            'notificationURL': request.host_url + 'api/subscription/btcpay-webhook',
            'redirectURL': request.host_url + 'success',
            'metadata': {
                'user_id': str(user.id),
                'plan': plan,
                'payment_method': 'btcpay'
            }
        }
        
        headers = {
            'Authorization': f'token {BTCPAY_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        response = requests.post(
            f'{BTCPAY_SERVER_URL}/api/v1/stores/{BTCPAY_STORE_ID}/invoices',
            headers=headers,
            json=invoice_data
        )
        
        if response.status_code == 200:
            invoice = response.json()
            return jsonify({'invoice_url': invoice['checkoutLink']}), 200
        else:
            return jsonify({'message': 'Failed to create BTCPay invoice'}), 500
            
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@subscription_bp.route('/webhook', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.getenv('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError:
        return jsonify({'message': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'message': 'Invalid signature'}), 400
    
    # Handle the event
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        handle_successful_payment(session)
    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        handle_subscription_renewal(invoice)
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        handle_subscription_update(subscription)
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        handle_subscription_cancellation(subscription)
    
    return jsonify({'status': 'success'}), 200

@subscription_bp.route('/btcpay-webhook', methods=['POST'])
def btcpay_webhook():
    """Handle BTCPay Server webhooks"""
    try:
        data = request.get_json()
        
        if data.get('type') == 'InvoiceSettled':
            invoice_id = data.get('invoiceId')
            
            # Get invoice details from BTCPay Server
            headers = {
                'Authorization': f'token {BTCPAY_API_KEY}',
                'Content-Type': 'application/json'
            }
            
            response = requests.get(
                f'{BTCPAY_SERVER_URL}/api/v1/stores/{BTCPAY_STORE_ID}/invoices/{invoice_id}',
                headers=headers
            )
            
            if response.status_code == 200:
                invoice = response.json()
                handle_btcpay_payment(invoice)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        print(f"BTCPay webhook error: {e}")
        return jsonify({'message': str(e)}), 500

def handle_successful_payment(session):
    """Handle successful Stripe payment"""
    try:
        user_id = int(session['metadata']['user_id'])
        plan = session['metadata']['plan']
        
        user = User.query.get(user_id)
        if not user:
            return
        
        # Create or update subscription
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        if not subscription:
            subscription = Subscription(user_id=user_id)
            db.session.add(subscription)
        
        subscription.stripe_subscription_id = session.get('subscription')
        subscription.status = 'active'
        subscription.plan = plan
        subscription.payment_method = 'stripe'
        subscription.current_period_start = datetime.now()
        
        if plan == 'monthly':
            subscription.current_period_end = datetime.now() + timedelta(days=30)
        else:
            subscription.current_period_end = datetime.now() + timedelta(days=365)
        
        db.session.commit()
        
    except Exception as e:
        print(f"Error handling successful payment: {e}")

def handle_btcpay_payment(invoice):
    """Handle successful BTCPay payment"""
    try:
        metadata = invoice.get('metadata', {})
        user_id = int(metadata.get('user_id'))
        plan = metadata.get('plan')
        
        user = User.query.get(user_id)
        if not user:
            return
        
        # Create or update subscription
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        if not subscription:
            subscription = Subscription(user_id=user_id)
            db.session.add(subscription)
        
        subscription.status = 'active'
        subscription.plan = plan
        subscription.payment_method = 'btcpay'
        subscription.current_period_start = datetime.now()
        
        if plan == 'monthly':
            subscription.current_period_end = datetime.now() + timedelta(days=30)
        else:
            subscription.current_period_end = datetime.now() + timedelta(days=365)
        
        db.session.commit()
        
    except Exception as e:
        print(f"Error handling BTCPay payment: {e}")

def handle_subscription_renewal(invoice):
    """Handle subscription renewal"""
    try:
        customer_id = invoice['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            subscription = Subscription.query.filter_by(user_id=user.id).first()
            if subscription:
                subscription.current_period_start = datetime.fromtimestamp(invoice['period_start'])
                subscription.current_period_end = datetime.fromtimestamp(invoice['period_end'])
                db.session.commit()
                
    except Exception as e:
        print(f"Error handling subscription renewal: {e}")

def handle_subscription_update(subscription_data):
    """Handle subscription updates"""
    try:
        customer_id = subscription_data['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            subscription = Subscription.query.filter_by(user_id=user.id).first()
            if subscription:
                subscription.status = subscription_data['status']
                db.session.commit()
                
    except Exception as e:
        print(f"Error handling subscription update: {e}")

def handle_subscription_cancellation(subscription_data):
    """Handle subscription cancellation"""
    try:
        customer_id = subscription_data['customer']
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        
        if user:
            subscription = Subscription.query.filter_by(user_id=user.id).first()
            if subscription:
                subscription.status = 'cancelled'
                db.session.commit()
                
    except Exception as e:
        print(f"Error handling subscription cancellation: {e}")

@subscription_bp.route('/status', methods=['GET'])
@jwt_required()
def get_subscription_status():
    """Get user's subscription status"""
    try:
        user_id = get_jwt_identity()
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
        return jsonify({'message': str(e)}), 500

@subscription_bp.route('/cancel', methods=['POST'])
@jwt_required()
def cancel_subscription():
    """Cancel user's subscription"""
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        subscription = Subscription.query.filter_by(user_id=user_id).first()
        
        if not subscription:
            return jsonify({'message': 'No active subscription found'}), 404
        
        if subscription.payment_method == 'stripe' and subscription.stripe_subscription_id:
            # Cancel Stripe subscription
            stripe.Subscription.delete(subscription.stripe_subscription_id)
        
        # Update local subscription status
        subscription.status = 'cancelled'
        db.session.commit()
        
        return jsonify({'message': 'Subscription cancelled successfully'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

