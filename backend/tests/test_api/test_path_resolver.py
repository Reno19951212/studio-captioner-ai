import pytest
from app.services.path_resolver import PathResolver


def test_resolve_client_to_server_path():
    resolver = PathResolver(
        server_base="/data/media",
        client_mounts={"/Volumes/MediaShare": "/data/media", "Z:\\": "/data/media"},
    )
    result = resolver.to_server_path("/Volumes/MediaShare/input/video.mxf")
    assert result == "/data/media/input/video.mxf"
    result = resolver.to_server_path("Z:\\input\\video.mxf")
    assert result == "/data/media/input/video.mxf"


def test_resolve_server_to_client_path():
    resolver = PathResolver(server_base="/data/media", client_mounts={"/Volumes/MediaShare": "/data/media"})
    result = resolver.to_client_path("/data/media/output/result.mp4", "/Volumes/MediaShare")
    assert result == "/Volumes/MediaShare/output/result.mp4"


def test_server_local_path_unchanged():
    resolver = PathResolver(server_base="/data/media", client_mounts={})
    result = resolver.to_server_path("/data/media/input/video.mxf")
    assert result == "/data/media/input/video.mxf"


def test_unknown_mount_raises():
    resolver = PathResolver(server_base="/data/media", client_mounts={"/Volumes/MediaShare": "/data/media"})
    with pytest.raises(ValueError, match="Cannot resolve"):
        resolver.to_server_path("/Users/someone/Desktop/video.mxf")
