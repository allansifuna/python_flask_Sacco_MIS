from kenversity import create_app
create_app("dev").app_context().push()
from kenversity.models import Deposit,Transaction,Member
from kenversity.member.utils import get_random_date
from random import choice
values=[1,2,3,4,5,6,7,8,9,0,"A","B","C","D","E","F","H","G","I","J","K","L","M","N","O","P","Z","R","S","T"]
members=Member.query.filter_by(status="ACTIVE").all()
for member in members:
    for i in range(20):
        date_created=get_random_date()
        code=["Q"]
        for i in range(9):
            code.append(str(choice(values)))

        vs=[1,2,3,4,5,6,7,8,9,0]
        chrid=[]
        for i in range(5):
            chrid.append(str(choice(vs)))
        chrid="".join(chrid)
        transaction=Transaction(transaction_code="".join(code),phone_number=member.phone_number,amount=choice([1000,2500,1700,1600,2000,1500]),reason="DEP",date_created=date_created)
        transaction.save()
        dep=Deposit(memberID=member.id,CheckoutRequestID=f"ws_CO_061020222032{chrid}{transaction.phone_number[3:]}",transactionID=transaction.id,amount=transaction.amount,deposit_date=date_created)
        dep.save()
