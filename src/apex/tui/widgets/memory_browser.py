"""Memory browser widget for TUI."""

import json
from typing import Any, Dict, List, Optional, Set

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Input, Static, Tree
from textual.widgets.tree import TreeNode


class MemoryBrowserWidget(Horizontal):
    """Widget for browsing LMDB memory hierarchically."""

    selected_key: reactive[Optional[str]] = reactive(None)
    search_query: reactive[str] = reactive("")
    auto_refresh: reactive[bool] = reactive(True)

    def __init__(self, lmdb_client: Optional[Any] = None, **kwargs) -> None:
        """Initialize with optional LMDB client."""
        super().__init__(**kwargs)
        self.lmdb_client = lmdb_client
        self.refresh_timer: Optional[Timer] = None
        self.expanded_nodes: Set[str] = set()  # Track expanded nodes

    def compose(self) -> ComposeResult:
        """Compose the memory browser layout."""
        with Vertical(id="memory-tree-container"):
            yield Static("[bold cyan]Memory Browser[/bold cyan]", id="memory-header")
            yield Input(placeholder="Search keys...", id="memory-search")
            yield Tree("Memory", id="memory-tree")

        with Vertical(id="memory-content-container"):
            yield Static("[bold cyan]Content Viewer[/bold cyan]", id="content-header")
            yield Static("", id="memory-content")

    def on_mount(self) -> None:
        """Initialize the tree when mounted."""
        self.load_memory_tree()

        # Connect tree selection event
        tree = self.query_one("#memory-tree", Tree)
        tree.focus()

        # Set up auto-refresh
        if self.auto_refresh:
            self.refresh_timer = self.set_interval(5.0, self.auto_refresh_tree)

    def on_unmount(self) -> None:
        """Clean up when unmounted."""
        if self.refresh_timer:
            self.refresh_timer.stop()

    async def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "memory-search":
            self.search_query = event.value
            self.load_memory_tree()

    async def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection."""
        node = event.node
        if node.data and isinstance(node.data, dict) and "key" in node.data:
            self.selected_key = node.data["key"]
            await self.load_key_content(node.data["key"])

    def load_memory_tree(self) -> None:
        """Load the memory tree structure."""
        if not self.lmdb_client:
            return

        try:
            tree = self.query_one("#memory-tree", Tree)

            # Save expanded state before clearing
            self._save_expanded_state(tree.root)

            tree.clear()

            # Get all keys
            keys = self.lmdb_client.list_keys("")

            # Filter keys if search query exists
            if self.search_query:
                filtered_keys = [
                    k for k in keys if self.search_query.lower() in k.lower()
                ]
                # Also include parent paths for context
                expanded_keys = set()
                for key in filtered_keys:
                    parts = key.strip("/").split("/")
                    for i in range(1, len(parts) + 1):
                        expanded_keys.add("/" + "/".join(parts[:i]))
                keys = sorted(list(expanded_keys))

            # Build tree structure
            tree_data = self._build_tree_structure(keys)

            # Populate tree widget
            self._populate_tree(tree.root, tree_data)

            # Restore expanded state
            self._restore_expanded_state(tree.root)

        except Exception:
            pass

    def _save_expanded_state(self, node: TreeNode, path: str = "") -> None:
        """Save which nodes are expanded."""
        if node.is_expanded:
            self.expanded_nodes.add(path)

        for child in node.children:
            child_path = f"{path}/{child.label}" if path else child.label
            self._save_expanded_state(child, child_path)

    def _restore_expanded_state(self, node: TreeNode, path: str = "") -> None:
        """Restore expanded state of nodes."""
        if path in self.expanded_nodes:
            node.expand()

        for child in node.children:
            child_path = f"{path}/{child.label}" if path else child.label
            self._restore_expanded_state(child, child_path)

    def _build_tree_structure(self, keys: List[str]) -> Dict[str, Any]:
        """Build hierarchical tree structure from flat keys."""
        tree = {}

        for key in sorted(keys):
            parts = key.strip("/").split("/")
            current = tree

            for i, part in enumerate(parts):
                if part not in current:
                    current[part] = {"_children": {}, "_is_leaf": i == len(parts) - 1}
                    if i == len(parts) - 1:
                        current[part]["_key"] = key
                current = current[part]["_children"]

        return tree

    def _populate_tree(self, parent_node: TreeNode, tree_data: Dict[str, Any]) -> None:
        """Populate tree widget from tree data."""
        for name, data in tree_data.items():
            if name.startswith("_"):
                continue

            # Determine node label and icon
            is_leaf = data.get("_is_leaf", False)
            icon = "📄" if is_leaf else "📁"
            label = f"{icon} {name}"

            # Add node
            if is_leaf and "_key" in data:
                node = parent_node.add(label, data={"key": data["_key"]})
            else:
                node = parent_node.add(label)

            # Add children
            if "_children" in data and data["_children"]:
                self._populate_tree(node, data["_children"])

    async def load_key_content(self, key: str) -> None:
        """Load and display content for selected key."""
        if not self.lmdb_client:
            return

        content_widget = self.query_one("#memory-content", Static)

        try:
            value = await self.lmdb_client.read(key)

            if value is None:
                content_widget.update("[red]Key not found[/red]")
                return

            # Try to format as JSON
            try:
                data = json.loads(value.decode() if isinstance(value, bytes) else value)
                formatted = json.dumps(data, indent=2)

                # Syntax highlight JSON (simple version)
                formatted = formatted.replace('":', '":')
                formatted = formatted.replace('": ', '": [green]')
                formatted = formatted.replace(",\n", "[/green],\n")
                formatted = formatted.replace("}\n", "[/green]}\n")
                formatted = formatted.replace("]\n", "[/green]]\n")

                content_widget.update(
                    f"[bold]Key:[/bold] [cyan]{key}[/cyan]\n\n"
                    f"[bold]Content:[/bold]\n{formatted}"
                )

            except (json.JSONDecodeError, UnicodeDecodeError):
                # Display as plain text
                content = value.decode() if isinstance(value, bytes) else str(value)
                content_widget.update(
                    f"[bold]Key:[/bold] [cyan]{key}[/cyan]\n\n"
                    f"[bold]Content:[/bold]\n[yellow]{content}[/yellow]"
                )

        except Exception as e:
            content_widget.update(f"[red]Error loading content: {e}[/red]")

    def refresh_tree(self) -> None:
        """Refresh the memory tree."""
        self.load_memory_tree()

    def auto_refresh_tree(self) -> None:
        """Auto-refresh the tree if enabled."""
        if self.auto_refresh:
            self.load_memory_tree()
