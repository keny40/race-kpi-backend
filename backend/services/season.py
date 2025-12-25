from datetime import datetime

class SeasonManager:
    @staticmethod
    def get_status():
        """
        현재 시즌 상태 요약
        (임시 구현 – 이후 scheduler / reset 로직과 연결)
        """
        return {
            "season": datetime.now().strftime("%Y"),
            "state": "ACTIVE",
            "updated_at": datetime.utcnow().isoformat()
        }
