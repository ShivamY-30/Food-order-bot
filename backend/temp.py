import mysql.connector
global cnx
#
cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    # database="pandeyji_eatery"
)

cursor = cnx.cursor()

    # Executing the SQL query to fetch the order status
query = f"SELECT * FROM pandeyji_eatery.order_tracking where order_id = 40;"
cursor.execute(query)

    # Fetching the result
result = cursor.fetchone()

    # Closing the cursor
cursor.close()

    # Returning the order status
if result:
    print(result[1])
else:
    print("false")

print("hello")
