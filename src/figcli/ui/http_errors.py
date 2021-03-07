class Error:
    KMS_DENIED = {'is_error': True, 'code': 'no-kms-access',
                  'message': 'Provided role does not have access to decrypt the specified configuration.',
                  'status_code': 403}, 200  # This is an 'expected' error, not a REAL error, so we return a 200
