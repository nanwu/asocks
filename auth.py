
class NoAuthRequired:
    method_code = 0 

acceptable_auth_methods = [NoAuthRequired]
acceptable_auth_method_codes = [method.method_code for method in acceptable_auth_methods]

    
