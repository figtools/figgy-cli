class Error:
    KMS_DENIED = {'error_code': 'KMS_DENIED',
                  'message': 'Provided role does not have access to decrypt the specified configuration.',
                  'status_code': 403}
    PARAM_ACCESS_DENIED = {'error_code': 'PARAM_ACCESS_DENIED',
                           'message': 'Provided role does not have access to perform the attempted action on the '
                                      'specified configuration',
                           'status_code': 403}

    FIG_MISSING = {'error_code': 'FIG_MISSING',
                   'message': 'Target configuration does not exist in parameter store.',
                   'status_code': 200}

    FIG_INVALID = {'error_code': 'FIG_INVALID',
                   'message': 'Provided configuration is invalid and cannot be saved to ParameterStore.',
                   'status_code': 400}

    MFA_REQUIRED = {'error_code': 'MFA_REQUIRED',
                    'message': 'MFA is required for authorization.',
                    'status_code': 401}

    FORCE_REAUTHENTICATION = {'error_code': 'FORCE_REAUTH',
                              'message': 'Please reauthenticate.',
                              'status_code': 401}

    BAD_REQUEST = {'error_code': 'BAD_REQUEST',
                     'message': 'Invalid request submitted.',
                     'status_code': 400}

    OTS_MISSING = {'error_code': 'OTS_MISSING',
                   'message': 'The value associated with the provided ID does not exist, has already been retrieved, '
                              'or has expired.',
                   'status_code': 200}