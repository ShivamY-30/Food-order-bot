from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db_helper
import Generic_helper

app = FastAPI()


inprogress_order = {}


@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']

    session_id = Generic_helper.extract_session_id(output_contexts[0]['name'])

    intent_handler_dict = {
        'order.add- content: ongoing-order': add_to_order,
        # 'order.remove- content: ongoing-order' : remove_from_order,
        'Order.complete - content: ongoing-order': complete_order,
        'track.order- content: ongoing-tracking': track_order

    }
    return intent_handler_dict[intent](parameters, session_id)

    # Initial approach
    # if intent == "track.order- content: ongoing-tracking":
    #     return track_order(parameters)


def add_to_order(parameters: dict, session_id: str):
    food_item = parameters["food-item"]
    food_quantity = parameters["number"]

    if len(food_item) != len(food_quantity):
        fulfillment_text = "Sorry You had not specified the quantity of food properly. Please try again"
    else:
        new_food_dict = dict(zip(food_item, food_quantity))

        if session_id in inprogress_order:
            current_food_dict = inprogress_order[session_id]
            current_food_dict.update(new_food_dict)
            inprogress_order[session_id] = current_food_dict
            pass
        else:
            inprogress_order[session_id] = new_food_dict

        order_str = Generic_helper.get_str_from_food_dict(inprogress_order[session_id])
        fulfillment_text = f"So far you have {order_str} Do you need anything else? "

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })


def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_order:
        fulfillment_text = "We are getting trouble in finding your order! Please try to order again"
    else:
        order = inprogress_order[session_id]
        order_id = save_to_db(order)

        if order_id == -1:
            fulfillment_text = "Sorry we cant process your order due to server side error Please try after some times"
        else:
            order_total = db_helper.get_total_order_price(order_id)
            fulfillment_text = f"Awesome Your order is placed. " \
                               f"Here is your order id {order_id}. " \
                               f"The total amount for your order is {order_total} which you can pay at time of delivery"
        del inprogress_order[session_id]
    return JSONResponse(content={
        "fulfillment_text": fulfillment_text
    })


def save_to_db(order: dict):
    next_order_id = db_helper.get_next_order_id()

    for food_item, food_quantity in order.items():
        rcode = db_helper.insert_order_item(
            food_item,
            food_quantity,
            next_order_id
        )
        if rcode == -1:
            return -1

    db_helper.insert_order_tracking(next_order_id, "in progress")

    return next_order_id


def track_order(parameters: dict, session_id: str):
    order_id = int(parameters['number'])
    order_status = db_helper.get_order_status(order_id)
    if order_status:
        fulfillment_text = f"The order status for Your Entered Order id: {order_id} is : {order_status}"
    else:
        fulfillment_text = f"We are facing some error please check whether Your entered order id is right or not!"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

# if __name__ =="__main__":
#     print(
#         Generic_helper.extract_session_id("projects/food-order-bot-cn9g/agent/sessions/123456/contexts/ongoing-order"))
