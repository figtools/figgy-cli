class Error:
    KMS_DENIED = {'error_code': 'no-kms-access',
                  'message': 'Provided role does not have access to decrypt the specified configuration.',
                  'status_code': 403}
    GET_PARAM_DENIED = {'error_code': 'get-denied',
                  'message': 'Provided role does not have access to get the specified configuration.',
                  'status_code': 403}