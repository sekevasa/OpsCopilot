"""Application services for AI runtime."""

import json
import time
from typing import Dict, Any
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from shared.domain_models import ServiceError
from ..domain.models import AIModel, InferenceJob, InferenceStatus, ModelStatus
from ..domain.repositories import AIModelRepository, InferenceJobRepository


class AIRuntimeService:
    """Service for managing AI model inference."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.model_repo = AIModelRepository(session)
        self.job_repo = InferenceJobRepository(session)

    async def register_model(
        self,
        name: str,
        version: str,
        model_type: str,
        description: str | None = None,
        input_schema: Dict[str, Any] | None = None,
        output_schema: Dict[str, Any] | None = None,
        hyperparameters: Dict[str, Any] | None = None,
    ) -> AIModel:
        """
        Register a new AI model.

        Args:
            name: Model name
            version: Model version
            model_type: Type of model
            description: Model description
            input_schema: Input schema
            output_schema: Output schema
            hyperparameters: Hyperparameters

        Returns:
            Registered model
        """
        existing = await self.model_repo.get_by_name(name)
        if existing:
            raise ServiceError(
                "DUPLICATE",
                f"Model '{name}' already exists",
                {"name": name}
            )

        model = AIModel(
            id=uuid4(),
            name=name,
            version=version,
            model_type=model_type,
            description=description,
            input_schema=input_schema,
            output_schema=output_schema,
            hyperparameters=hyperparameters,
            status=ModelStatus.AVAILABLE,
        )

        return await self.model_repo.create(model)

    async def get_model(self, name: str) -> AIModel:
        """Get model by name."""
        model = await self.model_repo.get_by_name(name)
        if not model:
            raise ServiceError(
                "NOT_FOUND",
                f"Model '{name}' not found",
                {"name": name}
            )
        return model

    async def run_inference(
        self,
        model_name: str,
        input_data: Dict[str, Any],
        timeout_seconds: int = 30,
    ) -> InferenceJob:
        """
        Run inference on model.

        Args:
            model_name: Name of model to use
            input_data: Input data for inference
            timeout_seconds: Inference timeout

        Returns:
            Inference job result
        """
        # Get model
        model = await self.get_model(model_name)

        # Create job
        job = InferenceJob(
            id=uuid4(),
            model_id=model.id,
            model_name=model_name,
            status=InferenceStatus.RUNNING,
            input_data=input_data,
            started_at=datetime.utcnow(),
        )

        job = await self.job_repo.create(job)

        try:
            # Simulate inference (in production, would load actual model)
            start_time = time.time()

            # Mock inference - just echo input back
            output_data = {
                "prediction": self._mock_prediction(input_data),
                "confidence": 0.95,
            }

            execution_time = int((time.time() - start_time) * 1000)

            # Update job
            await self.job_repo.update(
                job.id,
                {
                    "status": InferenceStatus.COMPLETED,
                    "output_data": output_data,
                    "execution_time_ms": execution_time,
                    "completed_at": datetime.utcnow(),
                }
            )

        except Exception as e:
            await self.job_repo.update(
                job.id,
                {
                    "status": InferenceStatus.FAILED,
                    "error_message": str(e),
                    "completed_at": datetime.utcnow(),
                }
            )
            raise ServiceError(
                "INFERENCE_FAILED",
                f"Inference failed: {str(e)}",
                {"model": model_name, "error": str(e)}
            )

        return await self.job_repo.get_by_id(job.id)

    def _mock_prediction(self, input_data: Dict[str, Any]) -> float:
        """Mock prediction logic."""
        # Sum all numeric values as simple prediction
        total = sum(v for v in input_data.values()
                    if isinstance(v, (int, float)))
        return float(total)
