from kenversity import create_app
create_app("dev").app_context().push()
from kenversity.models import Member,Transaction
from kenversity import bcrypt
from random import choice
id_front="7c8ecb9c9f46fe9a.jpg"
id_back="71c85022efe1c984.jpg"
kra_pin="c0ea9dd9d65fa182.pdf"
nums=[1,2,3,4,5,6,7,8,9]
values=[1,2,3,4,5,6,7,8,9,0,"A","B","C","D","E","F","H","G","I","J","K","L","M","N","O","P","Z","R","S","T"]
names=[('Geofrey','Pkiach'),('John','Doe'),('Melvin','Kimathi'),('Steve','Ndegwa'),('James','Kamau'),('Joseph','Kimani'),('Mercy','Mureithi'),('Elizabeth','Kamau'),('Sandra','Tacko'),('Joan','Adhiambo'),('June','Akinyi'),('Diana','Chelang\'at'),('Elizabeth','Chepkoech'),('Faith','Nekesa'),('Bradley','Jakait'),('Mark','Mlango'),('Nick','Ruto'),('Joseph','Wekesa'),('Nick','Orimbo'),('Hilda','Nasimiyu'),('Abel','Wafula'),('Hadija','Lule'),('Ashley','Kamau'),('Oscar','Ouma'),('Kingsley','Taabu'),('Samuel','Muli'),('Samuel','Ombati'),('Samuel','Kuria'),('Emmanuel','Chege'),('Emmanuel','Loperatum'),('Dominic','Marende'),('Remmington','Were'),('Kenneth','Bett'),('Arnold','Ombasa'),('Elizabeth','Wangunyu'),('Frank','Wafula'),('Robert','Wekesa'),('Monica','Nangila'),('Christine','Naliaka'),('Christine','Maina'),('Cornelius','Kundu'),('Dan','Shitawa'),('Robert','Kubasu')]
for name in names:
	fname=name[0]
	lname=name[1]
	phone=f"2547{''.join([str(choice(nums)) for i in range(8)])}"
	nat_id="".join([str(choice(nums)) for i in range(8)])
	email=f"{fname.lower()}{lname.lower()}@gmail.com"
	ps=f"{fname.lower()}123"
	passw=bcrypt.generate_password_hash(ps).decode("utf-8")
	member= Member(first_name = fname,last_name=lname,email=email,phone_number=phone,national_id=nat_id,id_front=id_front,id_back=id_back,kra_pin=kra_pin,password=passw)
	member.save()
	transaction=Transaction(transaction_code=f"Q{''.join([str(choice(values)) for i in range(9)])}",phone_number=phone,amount=1000,reason="REG")
	transaction.save()
	print(f"{transaction.transaction_code}")


