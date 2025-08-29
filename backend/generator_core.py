# backend/generator_core.py (Version 3 - Final, Context-Aware)
import inspect
import itertools
from copy import deepcopy
import typing

def get_base_type_name(annotation: any) -> str:
    origin = typing.get_origin(annotation)
    if origin is None:
        return getattr(annotation, '__name__', str(annotation))
    if origin is typing.Union:
        args = typing.get_args(annotation)
        base_type = next((arg for arg in args if arg is not type(None)), None)
        if base_type: return get_base_type_name(base_type)
    return getattr(origin, '__name__', str(origin))

# Accepts the `context` dictionary of real user classes
def capture_behavior_snapshots(target_func, plugins, context):
    sig = inspect.signature(target_func)
    params = list(sig.parameters.values())
    is_method = params and params[0].name in ('self', 'cls')
    
    if is_method:
        cls_name = target_func.__qualname__.split('.')[0]
        test_params = params[1:]
        all_params_for_conversion = params
        self_inputs_repr = plugins['INPUT_STRATEGIES'][cls_name]()
        arg_inputs_repr_lists = [plugins['INPUT_STRATEGIES'][get_base_type_name(p.annotation)]() for p in test_params]
        all_input_repr_lists = [self_inputs_repr] + arg_inputs_repr_lists
    else:
        all_params_for_conversion = params
        all_input_repr_lists = [plugins['INPUT_STRATEGIES'][get_base_type_name(p.annotation)]() for p in params]

    snapshots = []
    for input_combo_repr in itertools.product(*all_input_repr_lists):
        args = []
        for i, param in enumerate(all_params_for_conversion):
            base_type_name = get_base_type_name(param.annotation)
            converter = plugins['INPUT_CONVERTERS'].get(base_type_name, lambda x, ctx: x)
            # Pass the context to the converter
            args.append(deepcopy(converter(input_combo_repr[i], context)))

        def serialize_arg(arg):
            serializer = plugins['STATE_SERIALIZERS'].get(arg.__class__.__name__, lambda x, ctx: x)
            # Pass the context to the serializer
            return serializer(arg, context)

        before_states = [serialize_arg(arg) for arg in args]
        snapshot = {"inputs_repr": input_combo_repr, "return_value_repr": None, "after_states_repr": None, "exception": None}

        try:
            if is_method:
                instance, call_args = args[0], args[1:]
                result = getattr(instance, target_func.__name__)(*call_args)
            else:
                call_args = args
                result = target_func(*call_args)
            
            snapshot["return_value_repr"] = serialize_arg(result)
            snapshot["after_states_repr"] = [serialize_arg(arg) for arg in args]
        except Exception as e:
            snapshot["exception"] = repr(e)
            
        snapshots.append(snapshot)
    return snapshots