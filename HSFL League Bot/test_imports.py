try:
    from cogs.setup import SetupCommands, add_objects_database
    print("Setup cog imports OK")
except Exception as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
