# source: https://stackoverflow.com/a/70661458
import dataclasses, json

class TudriportJSONEncoder(json.JSONEncoder):
        def default(self, o):
            # Handle Dataclass instances
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            # To handle other objects, add branches like this
            #if isinstance(obj, Decimal):
            #    return str(obj)
            return super().default(o)
