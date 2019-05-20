#tracing call for Jaeger
#initializing the jaeger tracer
import logging
from jaeger_client import Config

def init_tracer(service):
    logging.getLogger('').handlers=[]
    logging.basicConfig(format='%(message)s', level=logging.DEBUG)

    config=Config(
        config={
            'sampler':{
                'type':'const',
                'param':1
            },
            'logging':True
        },
        service_name=service
    )

    return config.initialize_tracer()
