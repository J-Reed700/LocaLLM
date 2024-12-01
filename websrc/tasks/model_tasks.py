from websrc.config.celery_config import celery_app
from src.services.model_discovery_service import ModelDiscoveryService
from src.models.enum import ModelType
from src.dependencies.container import get_model_discovery_service

@celery_app.task(bind=True, name='download_model')
def download_model_task(self, model_id: str, model_type: str):
    try:
        model_service = get_model_discovery_service()
        model_type_enum = ModelType(model_type)
        
        # Run the download synchronously in the Celery worker
        import asyncio
        loop = asyncio.get_event_loop()
        loop.run_until_complete(
            model_service.download_model(model_id, model_type_enum)
        )
        
        return {
            'status': 'success',
            'model_id': model_id
        }
    except Exception as e:
        self.update_state(
            state='FAILURE',
            meta={
                'exc_type': type(e).__name__,
                'exc_message': str(e),
                'model_id': model_id
            }
        )
        raise 