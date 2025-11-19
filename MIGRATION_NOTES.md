# Migration Notes

## Renaming Project from helloworld to QueryCraft

If the `helloworld` folder still exists, you should rename it to `querycraft_project`:

```bash
mv helloworld querycraft_project
```

Or you can do this through your IDE.

All project files have been updated to reference `querycraft_project`.

## Removing hello app

The `hello` app is no longer used and can be removed:

```bash
rm -rf hello
```

Or you can do this through your IDE.
