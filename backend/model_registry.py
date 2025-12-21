# model_registry.py

class ModelRegistry:
    _models = {}

    @classmethod
    def register(cls, name: str, model):
        cls._models[name] = model

    @classmethod
    def get_models(cls):
        return cls._models


# 예시용 더미 모델 (실제 모델로 교체 가능)
class DummyModel:
    weight = 1.0

    def predict(self, payload: dict):
        return {
            "label": "P",
            "score": 0.6,
        }


# 서버 시작 시 기본 등록
ModelRegistry.register("model_A", DummyModel())
ModelRegistry.register("model_B", DummyModel())
ModelRegistry.register("model_C", DummyModel())
