from typing import Dict, Any

def get_config(env: str) -> Dict[str, Any]:
    base_config = {
        'project_name': 'AssistedWayfinding',
        'lambda_runtime': 'python3.9',
        'lambda_handler': 'index.handler',
        'environment': env,
    }

    env_specific_config = {
        'dev': {
            'lambda_memory_size': 128,
            'lambda_timeout': 30,
            'face_recognition': {
                'min_confidence': 70,
            }
        },
        'prod': {
            'lambda_memory_size': 256,
            'lambda_timeout': 60,
            'face_recognition': {
                'min_confidence': 90,
            }
        }
    }

    return {**base_config, **env_specific_config.get(env, env_specific_config['dev'])}