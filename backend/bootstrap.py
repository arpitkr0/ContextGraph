from backend.ingestion.file_manager import reset_to_demo, source_dir
from backend.ingestion.graph_builder import build_state_from_sources, replace_graph_state


def main() -> None:
    reset_to_demo()
    state = replace_graph_state(build_state_from_sources(source_dir()))
    print(f"Built graph: {len(state.assets)} assets, {len(state.edges)} relationships, {len(state.column_edges)} column edges")


if __name__ == "__main__":
    main()
