"""Path resolver — converts between client mount paths and server paths."""

from typing import Dict


class PathResolver:
    def __init__(self, server_base: str, client_mounts: Dict[str, str]):
        self.server_base = server_base
        self.client_mounts = client_mounts

    def to_server_path(self, client_path: str) -> str:
        normalized = client_path.replace("\\", "/")
        if normalized.startswith(self.server_base):
            return normalized
        for mount, server_path in self.client_mounts.items():
            mount_normalized = mount.replace("\\", "/").rstrip("/")
            if normalized.startswith(mount_normalized):
                relative = normalized[len(mount_normalized):]
                return server_path.rstrip("/") + relative
        raise ValueError(f"Cannot resolve path: {client_path}")

    def to_client_path(self, server_path: str, client_mount: str) -> str:
        if not server_path.startswith(self.server_base):
            raise ValueError(f"Path not under server base: {server_path}")
        relative = server_path[len(self.server_base):]
        return client_mount.rstrip("/") + relative
