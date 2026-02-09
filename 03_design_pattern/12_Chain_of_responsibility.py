"""
Chain of Responsibility Pattern
The Chain of Responsibility pattern is a behavioral design pattern that
allows an object to send a command without knowing which object will handle the request.
The request is passed along a chain of potential handlers until one of them handles it.
In the context of web development, this pattern is often used in middleware,
request handling, and permission systems.
Each handler in the chain can either process the request or pass it to the next handler.

Here's a simple implementation of the Chain of Responsibility pattern in Python:
"""


class Handler:
    def __init__(self, successor=None):
        self.successor = successor

    def handle(self, request):
        if self.successor:
            return self.successor.handle(request)
        return None

class ConcreteHandlerA(Handler):
    def handle(self, request):
        if request == "A":
            return "Handler A processed the request."
        else:
            return super().handle(request)

class ConcreteHandlerB(Handler):
    def handle(self, request):
        if request == "B":
            return "Handler B processed the request."
        else:
            return super().handle(request)

class ConcreteHandlerC(Handler):
    def handle(self, request):
        if request == "C":
            return "Handler C processed the request."
        else:
            return super().handle(request)


# Client code
if __name__ == "__main__":
    # Create handlers
    handler_c = ConcreteHandlerC()
    handler_b = ConcreteHandlerB(successor=handler_c)
    handler_a = ConcreteHandlerA(successor=handler_b)

    # Create requests
    requests = ["A", "B", "C", "D"]

    for request in requests:
        result = handler_a.handle(request)
        if result:
            print(result)
        else:
            print(f"No handler could process the request: {request}")
