# MapEdit
MapEdit is a single file ascii art editor written in Python. Think 'MS Paint' but instead of painting with pixels MapEdit paints with ASCII characters.

## Art Editor Features:

Save/Load
Undo/Redo
Hotkeys
Paint Tool
Line Tool
Fill (4-way) Tool
Fill (8-way) Tool
Square Tool
Box Tool

MapEdit can also freely switch into and out of 'Screen Mode'. 'Screen Mode' subdivides the canvas into smaller sections called 'Screens'. Each 'Screen' can be worked on independently with changes being limited to the area of the canvas that the selected 'Screen' represents. This is useful for: packed animations, tilemaps, game screens, etc.

MapEdit saves work in the json file format using row based run-length encoding.

For a demonstration of MapEdit Art Editor features see [this video.](https://youtu.be/0F21j_yh_ok)

## Code Features:

When imported as a module me.py provides the MapModel class which can be used to create, edit, save, load MapEdit art files programmatically. MapModel exposes all of the tools available to the art editor such as: line, fill, square, box, etc.

For example:
```
  import me


  # Create a ASCII map 20 by 20 in size and fill it with ' '

  m = me.MapModel(20, 20, ' ')


  # Draw a 5 by 5 empty rectangle starting at cell 6,6.
  # Note: this doesn't change the map it just finds the
  # cells that would need to be changed.

  rectangle = m.rectangle(6, 6, 11, 11, '!', filled = False)


  # This changes the map

  m.set_cells(rectangle)


  # Fill the area outside the rectangle.

  flood = m.flood_fill(0, 0, '.')
  m.set_cells(flood)

  
  # Draw a line from 13,18 to 4,2

  line = m.line(13, 18, 4, 2, '"')
  m.set_cells(line)


  # Convert the map to a string and print it

  print(m.to_string())
  ```
