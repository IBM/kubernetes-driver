example_kube_config = {
                    'apiVersion': 'v1',
                    'clusters': [
                        {'cluster': {'server': 'localhost'}, 'name': 'kubernetes'}
                    ],
                    'contexts': [
                        {'context': {'cluster': 'kubernetes', 'user': 'kubernetes-admin'}, 'name': 'kubernetes-admin@kubernetes'}
                    ],
                    'current-context': 'kubernetes-admin@kubernetes',
                    'kind': 'Config',
                    'preferences': {},
                    'users': [
                        {'name': 'kubernetes-admin', 'user': {}}
                    ]
                }