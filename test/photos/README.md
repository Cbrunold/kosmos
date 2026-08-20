# Real-table geometry fixtures

`railbirds-geometry.json` is a broadcast still of a 9-ft table — a Railbirds
production, white cloth, shot from behind the end rail — reduced to the only
numbers the importer's geometry actually needs: the four cloth corners and the
six ball centres, in the original frame's pixels, read off the photograph.

It exists because this exact shot broke the importer twice, and neither break
was visible in any scene rendered here:

* Filming square-on to the end rail leaves the across-the-table vanishing point
  at infinity, so the focal length could not be recovered from two orthogonal
  vanishing points. The importer fell back to assuming a phone lens and put the
  camera 0.89 m high and five metres off the side of a table 1.27 m wide.
* The table's length runs away from the camera, not across the frame. Clicking
  the corners in the order the workbench asks for laid the 2.54 m length along
  a 1.27 m rail, and no amount of dragging can repair that.

Run it against the built page:

    node test/photos/check-geometry.cjs

It should report the camera about 2.9 m behind the end rail, roughly a metre
up and near the centre line, with every ball on the cloth and each one
re-projecting to the pixel it was read from.
