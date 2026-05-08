"""CargoDash: a modular pipeline for LLM training data synthesis & augmentation."""
from .core import Module, Port, Pipeline
from .data_utils import Schema, Batch
from .modules import RawDataSource, DataOutput, Processor, MapProcessor, Judge
from .voting import Vote

__all__ = [
    "Module", "Port", "Pipeline",
    "Schema", "Batch",
    "RawDataSource", "DataOutput", "Processor", "MapProcessor", "Judge",
    "Vote",
]

__version__ = "0.1.0"
