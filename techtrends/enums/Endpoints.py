from enum import Enum


class Endpoints(Enum):
    INDEX = "/"
    POST = "/<int:post_id>"
    ABOUT = "/about"
    CREATE = "/create"
    HEALTH = "health"
    METRICS = "metrics"
