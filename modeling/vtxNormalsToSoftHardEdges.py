#----------------------------------------------------------------------------------
#   SCRIPT          vtxNormalsToSoftHardEdges.py
#   AUTHOR          Zaitsev Evgeniy
#                   ev.zaitsev@gmail.com
#
#                   import vtxNormalsToSoftHardEdges; vtxNormalsToSoftHardEdges.convertNormals();
#----------------------------------------------------------------------------------

import maya.cmds as cmds
import maya.OpenMaya as OpenMaya

class convertNormals( object ):
    def __init__( self ):
        self.convertSelected()

    def convertSelected( self ):
        print(" -------------------- ")
        m_list = OpenMaya.MSelectionList()
        OpenMaya.MGlobal.getActiveSelectionList( m_list )
        m_listIt = OpenMaya.MItSelectionList( m_list ) 
        m_listback = []
        while not m_listIt.isDone():
            self.m_path  = OpenMaya.MDagPath()
            m_listIt.getDagPath( self.m_path )
            if ( self.m_path.hasFn( OpenMaya.MFn.kMesh ) ):
                print( "Soft/Hard set to mesh {}".format( self.m_path.fullPathName() ) )
                self.setSoftHard()
                m_listback.append( self.m_path.fullPathName() )
            m_listIt.next()
        cmds.select( clear = True )
        for m_obj in m_listback:
            cmds.select( m_obj, add = True )
        print(" -------------------- ")

    def setSoftHard( self ):
        # calculate Hard Edges
        m_hardEdges = []
        m_itEdgeIt     = OpenMaya.MItMeshEdge( self.m_path ) 
        self.m_fnMesh = OpenMaya.MFnMesh( self.m_path )
        while not m_itEdgeIt.isDone():
            m_facesArray = OpenMaya.MIntArray()
            m_edgeId = m_itEdgeIt.index()
            m_itEdgeIt.getConnectedFaces(m_facesArray)  
            m_start, m_end = self.getEdgeVertices( m_edgeId )
            m_state = self.isEdgeSmooth( m_edgeId, m_start, m_end, m_facesArray )
            if ( False == m_state ):
                m_hardEdges.append( m_edgeId )
            #print( m_edgeId, m_state, m_start, m_end, m_facesArray )
            m_itEdgeIt.next()
        # select and set Hard Edges 
        m_aMember           = ''
        m_lastIndices       = [ -1, -1 ]
        m_haveEdge          = False
        for m_edgeId in m_hardEdges:
            if ( -1 == m_lastIndices[0] ):
                m_lastIndices[0] = m_edgeId
                m_lastIndices[1] = m_edgeId
            else:
                m_currentIndex = m_edgeId
                if ( m_currentIndex > m_lastIndices[1] + 1 ):
                    m_aMember += '{0}.e[{1}:{2}] '.format( self.m_path.fullPathName(), m_lastIndices[0], m_lastIndices[1] )
                    m_lastIndices[0] = m_currentIndex
                    m_lastIndices[1] = m_currentIndex 
                else:
                    m_lastIndices[1] = m_currentIndex
            m_haveEdge = True
        if ( m_haveEdge ):
            m_aMember += '{0}.e[{1}:{2}] '.format( self.m_path.fullPathName(), m_lastIndices[0], m_lastIndices[1] )
        m_resultString = ""
        m_resultString += "select -r {};\n".format( self.m_path.fullPathName())
        m_resultString += "polyNormalPerVertex -ufn true;\n";
        m_resultString += "polySoftEdge -a 180 -ch 1;\n";
        m_resultString += "select -r {0};\n".format( m_aMember )
        m_resultString += "polySoftEdge -a 0 -ch 1;\n"
        m_resultString += "select -cl;"
        #print(m_resultString)
        OpenMaya.MGlobal.executeCommand( m_resultString )
    
    def getEdgeVertices( self, m_edgeId ):
        m_util = OpenMaya.MScriptUtil() 
        m_util.createFromList([0, 0], 2)
        m_ptr = m_util.asInt2Ptr()
        self.m_fnMesh.getEdgeVertices( m_edgeId, m_ptr )
        m_start = m_util.getInt2ArrayItem( m_ptr,0,0 )
        m_end = m_util.getInt2ArrayItem( m_ptr,0,1 )
        return m_start, m_end
        
    def isEdgeSmooth( self, m_edgeId, m_start, m_end, m_facesArray ):
        m_state = True
        m_normalStartArr = OpenMaya.MVectorArray()
        m_normalEndArr   = OpenMaya.MVectorArray()
        for m_faceId in m_facesArray:
            m_normalStart = OpenMaya.MVector()
            m_normalEnd   = OpenMaya.MVector()
            self.m_fnMesh.getFaceVertexNormal( m_faceId, m_start, m_normalStart, OpenMaya.MFn.kWorld )
            self.m_fnMesh.getFaceVertexNormal( m_faceId, m_end, m_normalEnd, OpenMaya.MFn.kWorld )
            m_normalStartArr.append( m_normalStart )
            m_normalEndArr.append(m_normalEnd)
        m_normalStart1 = m_normalStartArr[0]
        for i in range( m_normalStartArr.length() ):
            m_normalStart2 = m_normalStartArr[i]
            if ( m_normalStart1 != m_normalStart2 ):
                m_state = False
            m_normalStart1 = m_normalStart2
        m_normalEnd1 = m_normalEndArr[0]
        for i in range( m_normalEndArr.length() ):
            m_normalEnd2 = m_normalEndArr[i]
            if ( m_normalEnd1 != m_normalEnd2 ):
                m_state = False
            m_normalEnd1 = m_normalEnd2
        return m_state
