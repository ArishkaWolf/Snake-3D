"""Простые процедурные сетки. Модели не требуют Blender или файлов .egg."""
from math import cos, sin, pi, copysign
from panda3d.core import (Geom, GeomNode, GeomVertexData, GeomVertexFormat,
                          GeomVertexWriter, GeomTriangles, NodePath, TransparencyAttrib)

_SPHERES = {}


def mesh(name, vertices, normals, triangles):
    data = GeomVertexData(name, GeomVertexFormat.getV3n3(), Geom.UHStatic)
    vw, nw = GeomVertexWriter(data, "vertex"), GeomVertexWriter(data, "normal")
    for v, n in zip(vertices, normals):
        vw.addData3(*v)
        nw.addData3(*n)
    primitive = GeomTriangles(Geom.UHStatic)
    for triangle in triangles:
        primitive.addVertices(*triangle)
    geometry = Geom(data)
    geometry.addPrimitive(primitive)
    node = GeomNode(name)
    node.addGeom(geometry)
    return NodePath(node)


def sphere_template(exponent=1.0):
    if exponent in _SPHERES:
        return _SPHERES[exponent]
    vertices, normals, triangles = [], [], []
    rings, sides = 12, 20
    def power(v):
        return copysign(abs(v) ** exponent, v)
    for i in range(rings + 1):
        latitude = -pi / 2 + pi * i / rings
        for j in range(sides + 1):
            longitude = 2 * pi * j / sides
            unit = (cos(latitude) * cos(longitude), cos(latitude) * sin(longitude), sin(latitude))
            vertices.append(tuple(power(v) for v in unit))
            normal = tuple(copysign(abs(v) ** (2 - exponent), v) for v in unit)
            length = sum(v * v for v in normal) ** 0.5
            normals.append(tuple(v / length for v in normal))
    for i in range(rings):
        for j in range(sides):
            a = i * (sides + 1) + j
            b = a + sides + 1
            triangles.extend(((a, a + 1, b), (a + 1, b + 1, b)))
    node = mesh("rounded-form", vertices, normals, triangles)
    _SPHERES[exponent] = node
    return node


def ellipsoid(parent, pos, scale, color, exponent=1.0):
    node = sphere_template(exponent).copyTo(parent)
    node.setPos(*pos)
    node.setScale(*scale)
    node.setColor(*color)
    return node


def rounded_box(parent, pos, size, color, radius=0.15):
    """Низкая плита со скруглённым контуром и плоскими гранями."""
    w, d, height = size
    radius = min(radius, w / 2, d / 2)
    outline = []
    for cx, cy, start in ((w/2-radius, d/2-radius, 0), (-w/2+radius, d/2-radius, pi/2),
                          (-w/2+radius, -d/2+radius, pi), (w/2-radius, -d/2+radius, 3*pi/2)):
        for k in range(5):
            angle = start + k * pi / 8
            outline.append((cx + radius * cos(angle), cy + radius * sin(angle)))
    vertices, normals, triangles = [], [], []
    n = len(outline)
    vertices.append((0, 0, height / 2))
    normals.append((0, 0, 1))
    for x, y in outline:
        vertices.append((x, y, height/2))
        normals.append((0, 0, 1))
    for i in range(n):
        triangles.append((0, i+1, (i+1) % n+1))
        x1, y1 = outline[i]
        x2, y2 = outline[(i+1) % n]
        nx, ny = y2-y1, x1-x2
        length = (nx*nx+ny*ny)**0.5 or 1
        start = len(vertices)
        vertices.extend(((x1,y1,-height/2), (x2,y2,-height/2), (x2,y2,height/2), (x1,y1,height/2)))
        normals.extend([(nx/length,ny/length,0)]*4)
        triangles.extend(((start,start+1,start+2),(start,start+2,start+3)))
    node = mesh("rounded-slab", vertices, normals, triangles)
    node.reparentTo(parent)
    node.setPos(*pos)
    node.setColor(*color)
    return node


def torus(parent, pos, radius, thickness, color):
    """Кольцо в плоскости XZ: оправа очков и декор."""
    vertices, normals, triangles = [], [], []
    sides, tube = 28, 8
    for i in range(sides+1):
        a = 2*pi*i/sides
        for j in range(tube+1):
            b = 2*pi*j/tube
            vertices.append(((radius+thickness*cos(b))*cos(a), thickness*sin(b), (radius+thickness*cos(b))*sin(a)))
            normals.append((cos(b)*cos(a), sin(b), cos(b)*sin(a)))
    for i in range(sides):
        for j in range(tube):
            a = i*(tube+1)+j
            b = a+tube+1
            triangles.extend(((a,b,a+1),(a+1,b,b+1)))
    node = mesh("round-frame", vertices, normals, triangles)
    node.reparentTo(parent)
    node.setPos(*pos)
    node.setColor(*color)
    node.setTwoSided(True)
    return node


def shadow(parent, x, y, width=0.5, depth=0.45):
    node = ellipsoid(parent, (x,y,0.028), (width,depth,0.012), (0.15,0.23,0.19,0.13))
    node.setTransparency(TransparencyAttrib.MAlpha)
    node.setLightOff()
    node.setDepthWrite(False)
    return node


def rounded_card(width,height,color,radius=0.045):
    """Плоская скруглённая панель для DirectGUI, без растровых текстур."""
    radius=min(radius,width/2,height/2)
    outline=[]
    for cx,cz,start in ((width/2-radius,height/2-radius,0),(-width/2+radius,height/2-radius,pi/2),
                        (-width/2+radius,-height/2+radius,pi),(width/2-radius,-height/2+radius,3*pi/2)):
        for i in range(7):
            angle=start+i*pi/12
            outline.append((cx+radius*cos(angle),0,cz+radius*sin(angle)))
    vertices=[(0,0,0)]+outline
    triangles=[(0,i+1,(i+1)%len(outline)+1) for i in range(len(outline))]
    node=mesh("soft-ui-card",vertices,[(0,-1,0)]*len(vertices),triangles)
    node.setColor(*color)
    node.setLightOff()
    node.setTransparency(TransparencyAttrib.MAlpha)
    node.setDepthWrite(False)
    return node
