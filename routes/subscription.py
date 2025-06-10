from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

subscription_bp = Blueprint('subscription', __name__)

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
        return jsonify({'error': 'Failed to get plans'}), 500

@subscription_bp.route('/status', methods=['GET'])
@cross_origin()
def get_subscription_status():
    """Get user's subscription status"""
    try:
        return jsonify({
            'active': False,
            'plan': None,
            'status': 'none',
            'next_billing_date': None
        }), 200
    except Exception as e:
        print(f"Get status error: {e}")
        return jsonify({'error': 'Failed to get status'}), 500

@subscription_bp.route('/create', methods=['POST', 'OPTIONS'])
@cross_origin()
def create_subscription():
    """Create a new subscription"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        plan = data.get('plan')
        payment_method = data.get('payment_method', 'stripe')
        
        if not plan:
            return jsonify({'error': 'Plan is required'}), 400
            
        return jsonify({
            'message': 'Subscription created successfully',
            'subscription': {
                'id': 1,
                'plan': plan,
                'payment_method': payment_method,
                'status': 'active'
            }
        }), 201
        
    except Exception as e:
        print(f"Create subscription error: {e}")
        return jsonify({'error': 'Failed to create subscription'}), 500

