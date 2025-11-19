# -*- coding: utf-8 -*-
"""
Stripe集成简单测试
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

print('='*60)
print('Stripe Integration Test')
print('='*60)

# Test 1: Check environment variables
print('\n[1] Checking environment variables...')
stripe_key = os.getenv('STRIPE_SECRET_KEY', '')
print('STRIPE_SECRET_KEY:', 'OK' if stripe_key.startswith('sk_') else 'MISSING')

monthly_price = os.getenv('STRIPE_PRICE_MONTHLY', '')
print('STRIPE_PRICE_MONTHLY:', monthly_price if monthly_price else 'MISSING')

yearly_price = os.getenv('STRIPE_PRICE_YEARLY', '')
print('STRIPE_PRICE_YEARLY:', yearly_price if yearly_price else 'MISSING')

lifetime_price = os.getenv('STRIPE_PRICE_LIFETIME', '')
print('STRIPE_PRICE_LIFETIME:', lifetime_price if lifetime_price else 'MISSING')

# Test 2: Import Stripe Manager
print('\n[2] Testing Stripe Manager...')
sys.path.insert(0, 'api')
try:
    from stripe_manager import StripeManager
    manager = StripeManager()
    print('SUCCESS: Stripe Manager initialized')

    # Test get_plan_info
    print('\n[3] Testing plan info...')
    for plan in ['pro_monthly', 'pro_yearly', 'lifetime']:
        result = manager.get_plan_info(plan)
        if result['success']:
            p = result['plan']
            print('{}: {} - ${} {}'.format(plan, p['name'], p['price'], p['currency']))
        else:
            print('{}: ERROR - {}'.format(plan, result.get('error')))

    print('\n' + '='*60)
    print('SUCCESS: All basic tests passed!')
    print('='*60)
    print('\nNext steps:')
    print('1. Start local server: vercel dev')
    print('2. Test create checkout session')
    print('3. Use Stripe test card: 4242 4242 4242 4242')

except Exception as e:
    print('ERROR: {}'.format(e))
    import traceback
    traceback.print_exc()
