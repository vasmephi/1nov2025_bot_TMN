from yookassa import Payment, Configuration
from yookassa.domain.models.currency import Currency
from yookassa.domain.models.receipt import Receipt, ReceiptItem
from yookassa.domain.common.confirmation_type import ConfirmationType
from yookassa.domain.models.confirmation.request.confirmation_redirect import ConfirmationRedirect
import uuid
import config
import os
from database import db

Configuration.configure(
    account_id=os.getenv('YOOKASSA_SHOP_ID'),
    secret_key=os.getenv('YOOKASSA_SECRET_KEY')
)



class YooKassaPayment:
    def __init__(self):
        self.shop_id = config.YOOKASSA_SHOP_ID
        self.secret_key = config.YOOKASSA_SECRET_KEY
    
    def create_payment(self, user_id, amount, description="Оплата подписки"):
        # Создаем уникальный id для платежа
        idempotence_key = str(uuid.uuid4())
        
        payment = Payment.create({
            "amount": {
                "value": str(amount),
                "currency": Currency.RUB
            }
            # ,
            # "payment_method_data":{
            # "type":"bank_card"
            # }
            ,
            "confirmation": {
                "type": ConfirmationType.REDIRECT,
                "return_url": "https://t.me/ykassa11102025_bot"  # URL для возврата после оплаты
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": user_id
            }
        }, idempotence_key)
        
        return payment
    
    def check_payment_status(self, payment_id):
        payment = Payment.find_one(payment_id)
        return payment.status

# Глобальный экземпляр платежной системы
payment_system = YooKassaPayment()