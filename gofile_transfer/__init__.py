"""GoFile Fast Link Transfer library."""

from .pipeline import TransferPipeline, TransferSummary
from .downloader import ParallelDownloader
from .uploader import GoFileUploader, GoFileResult
from .streamer import DirectStreamPipe, StreamWrapper
from .resolvers import ResolverFactory, ResolvedURL

__version__ = "1.1.0"

__all__ = [
    "TransferPipeline",
    "TransferSummary",
    "ParallelDownloader",
    "GoFileUploader",
    "GoFileResult",
    "DirectStreamPipe",
    "StreamWrapper",
    "ResolverFactory",
    "ResolvedURL",
]
