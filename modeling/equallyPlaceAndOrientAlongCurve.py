#-----------------------------------------------------------------------------------
#
#   SCRIPT      equallyPlaceAndOrientAlongCurve.py
#   AUTHORS     Evgen Zaitsev
#               ev.zaitsev@gmail.com
#
#-----------------------------------------------------------------------------------
import maya.cmds as cmds
import maya.OpenMaya as OpenMaya
import math
# number of points along the curve
def main(m_amount = 32):
    # internally maya keeps everything in centimeters
    if ('m' == cmds.currentUnit( query=True, linear=True )):
        m_unitScale = 0.01
    else:
        m_unitScale = 1.0
    # process selection 
    m_selectionList = OpenMaya.MSelectionList()
    OpenMaya.MGlobal.getActiveSelectionList( m_selectionList )
    m_obj = OpenMaya.MObject() 
    # get first selected object
    try: 
        m_selectionList.getDependNode( 0, m_obj )
    except:
        pass
    if m_obj:
        # check if its kDagNode
        if m_obj.hasFn( OpenMaya.MFn.kDagNode ):
            m_path  = OpenMaya.MDagPath()
            # link MObject to MDagPath
            OpenMaya.MDagPath.getAPathTo( m_obj, m_path )
            # check if its a kNurbsCurve
            if m_path.hasFn( OpenMaya.MFn.kNurbsCurve ):
                #
                m_parent = cmds.createNode( 'transform', n='points')
                # conenct function set to this MDagPath
                m_fnNurbs = OpenMaya.MFnNurbsCurve(m_path)
                # finally we can do something
                #
                # we will need copy of this curve with offset to calculate tangents
                # 
                m_offsetCurve = cmds.offsetCurve( m_path.fullPathName())
                m_selOffset  = OpenMaya.MSelectionList()
                m_objOffset  = OpenMaya.MObject() 
                m_pathOffset = OpenMaya.MDagPath()
                # get MObject from string name
                m_selOffset.add(m_offsetCurve[0])  
                m_selOffset.getDependNode(0, m_objOffset) 
                # link MObject to MDagPath
                OpenMaya.MDagPath.getAPathTo( m_objOffset, m_pathOffset )
                # we know 100% its a kNurbsCurve
                m_fnNurbsOffset = OpenMaya.MFnNurbsCurve(m_pathOffset)
                #
                m_step = 1.0/float(m_amount-1)
                # iterate from 0 to m_amount-1
                m_points = []
                m_pointsOffset = []
                for i in range(m_amount):
                    # findParamFromLength - returns parameter value corrisponding to the given length
                    # problem is parameter is not normalized 
                    # its relative to the length of the curve
                    m_param = m_fnNurbs.findParamFromLength(m_fnNurbs.length()*i*m_step)
                    m_paramOffset = m_fnNurbsOffset.findParamFromLength(m_fnNurbsOffset.length()*i*m_step)
                    # from this parameter we can extract position
                    m_point = OpenMaya.MPoint()
                    m_pointOffset = OpenMaya.MPoint()
                    # 
                    m_fnNurbs.getPointAtParam(m_param,m_point,OpenMaya.MSpace.kWorld )
                    m_fnNurbsOffset.getPointAtParam(m_paramOffset,m_pointOffset,OpenMaya.MSpace.kWorld )
                    m_points.append(m_point)
                    m_pointsOffset.append(m_pointOffset)
                # iterate over points
                for i in range(len(m_points)):
                    #
                    # create transform
                    #
                    m_transform = cmds.createNode( 'transform', n='transform{}'.format(i), p=m_parent )
                    # set transaltion
                    cmds.setAttr("{}.translateX".format(m_transform),m_unitScale*m_points[i].x)
                    cmds.setAttr("{}.translateY".format(m_transform),m_unitScale*m_points[i].y)
                    cmds.setAttr("{}.translateZ".format(m_transform),m_unitScale*m_points[i].z)
                    #
                    # calculate rotation
                    #
                    # calculate tangent along the curve
                    if ((len(m_points)-1)==i):
                        m_point_curr = m_points[i-1]
                        m_point_next = m_points[i]
                    else:
                        m_point_curr = m_points[i]
                        m_point_next = m_points[i+1]
                    m_tangent = OpenMaya.MVector(0.0,0.0,0.0)
                    m_tangent = OpenMaya.MVector( (m_point_next-m_point_curr) )
                    m_tangent.normalize()
                    # calculate normal 
                    m_normal = OpenMaya.MVector(0.0,0.0,0.0)
                    m_point_curr = m_points[i]
                    m_point_currOffset = m_pointsOffset[i]
                    m_normal = OpenMaya.MVector( (m_point_currOffset-m_point_curr) )
                    m_normal.normalize()
                    # calculate up vector
                    m_up = OpenMaya.MVector(0.0,0.0,0.0)
                    m_up = m_tangent^m_normal
                    m_up.normalize()
                    # re-adjust normal
                    m_normal = m_up^m_tangent
                    m_normal.normalize()
                    #
                    # MTransformationMatrix
                    #
                    m_matrix = OpenMaya.MMatrix()
                    m_util = OpenMaya.MScriptUtil()
                    # create rotation matrix from list
                    m_list = [  m_tangent.x,m_tangent.y,m_tangent.z,0.0,
                                m_up.x,m_up.y,m_up.z,0.0,
                                m_normal.x,m_normal.y,m_normal.z,0.0,
                                0.0,0.0,0.0,0.0]
                    m_util.createMatrixFromList(m_list,m_matrix)
                    # create MTransformationMatrix
                    m_matrixTr = OpenMaya.MTransformationMatrix(m_matrix)
                    m_eulerRot = m_matrixTr.eulerRotation()
                    # set rotation
                    cmds.setAttr("{}.rotateX".format(m_transform),math.degrees(m_eulerRot.x))
                    cmds.setAttr("{}.rotateY".format(m_transform),math.degrees(m_eulerRot.y))
                    cmds.setAttr("{}.rotateZ".format(m_transform),math.degrees(m_eulerRot.z))
                    # display them in viewport
                    cmds.setAttr("{}.displayLocalAxis".format(m_transform),1)
                    cmds.setAttr("{}.displayHandle".format(m_transform),1)
                # delete helping curve
                cmds.delete(m_pathOffset.fullPathName())
                cmds.select(m_parent,r=True)
                
main()