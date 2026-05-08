amount = float(input("Enter purchase amount: "))

if amount >= 1000:
    discount = amount * 0.20   
elif amount >= 500:
    discount = amount * 0.10   
else:
    discount = 0              

final_amount = amount - discount

print("Original Amount:", amount)
print("Discount:", discount)
print("Final Amount to Pay:", final_amount)
