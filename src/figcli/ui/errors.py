class Error:
    KMS_DENIED = {'error_code': 'KMS_DENIED',
                  'message': 'Provided role does not have access to decrypt the specified configuration.',
                  'status_code': 403}
    PARAM_ACCESS_DENIED = {'error_code': 'PARAM_ACCESS_DENIED',
                  'message': 'Provided role does not have access to perform the attempted action on the specified '
                             'configuration',
                  'status_code': 403}

    FIG_MISSING = {'error_code': 'FIG_MISSING',
                  'message': 'Target configuration does not exist in parameter store.',
                  'status_code': 200}