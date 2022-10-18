from kenversity import create_app
create_app("dev").app_context().push()
from kenversity.models import Deposit,Transaction
from random import choice
values=[1,2,3,4,5,6,7,8,9,0,"A","B","C","D","E","F","H","G","I","J","K","L","M","N","O","P","Z","R","S","T"]
for i in range(16):
    code=["Q"]
    for i in range(9):
        code.append(str(choice(values)))

    vs=[1,2,3,4,5,6,7,8,9,0]
    chrid=[]
    for i in range(5):
        chrid.append(str(choice(vs)))
    chrid="".join(chrid)
    transaction=Transaction(transaction_code="".join(code),phone_number="254713812939",amount=choice([1000,500,700,600,1500]),reason="DEP")
    transaction.save()
    dep=Deposit(memberID="24eb195def9696b5",CheckoutRequestID=f"ws_CO_061020222032{chrid}{transaction.phone_number[3:]}",transactionID=transaction.id,amount=transaction.amount)
    dep.save()
