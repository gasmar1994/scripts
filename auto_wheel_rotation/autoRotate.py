import textwrap

from maya import cmds
import utils.ar_utils as utils
reload(utils)


def base(wheel):
    '''Create base locators to measure wheel.'''
    if len(wheel) < 1:
        cmds.warning('Please select wheel(s).')
        return
        
    name = '{}_{}'.format(utils.side(wheel), utils.description(wheel))
    wheel
    # create group with locators and their respective distances
    dist1_locator, dist2_locator, center_locator, dist1, dist2, distance_grp = baseLocators(wheel)
    
    # create measure distance node and get diameter
    diameter = measureWheelDistance(wheel, dist1, dist2)

    # position the locators based on the wheel's bounding box
    utils.placeLocators(wheel, center_locator, dist1_locator, dist2_locator)
    cmds.parent(diameter, distance_grp)
    # center group pivot
    center_locator_transforms = cmds.xform(center_locator, query=True, translation=True)
    cmds.move(center_locator_transforms[0],
              center_locator_transforms[1],
              center_locator_transforms[2],
              '{}.scalePivot'.format(distance_grp),
              '{}.rotatePivot'.format(distance_grp),
              absolute=True)

    
def autoRotate(wheel):
    '''Create auto rotation based on diameter from base locators.'''
    if len(wheel) < 1:
        cmds.warning('Please select wheel(s).')
        return
        
    name = '{}_{}'.format(utils.side(wheel), utils.description(wheel))
    
    dist1_locator = '{}_wheelDist01_LOC'.format(name)
    dist2_locator = '{}_wheelDist01_LOC'.format(name)
    center_locator = '{}_wheelCenter_LOC'.format(name)
    distance_grp = '{}_locs_GRP'.format(name)
    distance = '{}_DIST'.format(name)
    
    cmds.select(clear=True)
    cmds.select(wheel)
    # create group that holds autoRotate connections
    auto_rotate_grp = autoRotateGrp(wheel)
    cmds.addAttr(auto_rotate_grp, longName='offset', attributeType='double', defaultValue=0)
    cmds.setAttr('{}.{}'.format(auto_rotate_grp, 'offset'), keyable=True)
    # create control to drive autoRotate grp
    auto_rotate_ctrl = autoRotateCtrl(center_locator, wheel)
    cmds.addAttr(auto_rotate_ctrl, longName='auto', attributeType='bool', defaultValue=1)
    cmds.setAttr('{}.{}'.format(auto_rotate_ctrl[0], 'auto'), keyable=True)
    cmds.makeIdentity(auto_rotate_ctrl, apply=True)
    # create group that drives the autoRotate group's orientation
    orient_grp = cmds.group(auto_rotate_grp, name='{}_orient_GRP'.format(name), 
                            relative=True)
    cmds.orientConstraint(auto_rotate_ctrl, orient_grp, maintainOffset=True)

    offset_ctrl = offsetCtrl(auto_rotate_ctrl, wheel)
    cmds.parent(center_locator, auto_rotate_ctrl[0])
    cmds.makeIdentity(offset_ctrl, apply=True)
    cmds.xform(offset_ctrl, centerPivots=True)
    utils.attrLockAndHide(offset_ctrl, 'tx ty tz ry rz sx sy sz v')

    # expression that drives autoRotate group's rotateX and offset attribute
    expression = wheelExpression('{}.rotateX'.format(auto_rotate_grp), 
                                 auto_rotate_ctrl[0], auto_rotate_grp, distance, wheel)

    center_locator_constraint = cmds.ls(center_locator, dagObjects=True)[-1]
    cmds.delete(center_locator_constraint)

    cmds.pointConstraint(center_locator, auto_rotate_grp)
    cmds.scaleConstraint(center_locator, auto_rotate_grp)

    cmds.parent(distance, auto_rotate_ctrl[0])
    cmds.parent(dist1_locator, dist2_locator, wheel)

    cmds.parent(wheel, offset_ctrl[0])
    cmds.parent(offset_ctrl[0], auto_rotate_grp)
    
    world_group_node = cmds.listRelatives(orient_grp, parent=True)
    cmds.parent(auto_rotate_ctrl[0], world_group_node)

    # cleanup
    cmds.setAttr('{}.visibility'.format(distance), 0)
    cmds.setAttr('{}.visibility'.format(center_locator), 0)
    cmds.setAttr('{}.visibility'.format(dist1_locator), 0)
    cmds.setAttr('{}.visibility'.format(dist2_locator), 0)
    cmds.delete(distance_grp)
    cmds.select(clear=True)

def deleteAutoRotate(wheel):
    '''Find and delete auto rotation system nodes'''
    if len(wheel) < 1:
        cmds.warning('Please select wheel(s).')
        return
        
    name = '{}_{}'.format(utils.side(wheel), utils.description(wheel))
    disconnect_nodes = []
    
    loc_grp = '{}_locs_GRP'.format(name)
    dist1_locator = '{}_wheelDist01_LOC'.format(name)
    dist2_locator = '{}_wheelDist02_LOC'.format(name)
    expression = '{}_autoRotate_EXP'.format(name)
    orient_grp = '{}_orient_GRP'.format(name)
    auto_rotate_control = '{}_autoRotate_CTRL'.format(name)
    world_group_node = '{}_WHEEL_GRP'.format(name)
    
    if cmds.objExists(wheel):
        if cmds.listRelatives(wheel, parent=True):
            cmds.parent(wheel, world=True)
    else:
        pass

    if cmds.objExists(expression):
        disconnect_nodes.append(expression)
    else:
        pass
        
    if cmds.objExists(orient_grp):
        disconnect_nodes.append(orient_grp)
    else:
        pass
        
    if cmds.objExists(auto_rotate_control):
        disconnect_nodes.append(auto_rotate_control)
    else:    
        pass
        
    if cmds.objExists(world_group_node):
        disconnect_nodes.append(world_group_node)
    else:
        pass
        
    if cmds.objExists(dist1_locator):
        disconnect_nodes.append(dist1_locator)
    else:
        pass
        
    if cmds.objExists(dist2_locator):
        disconnect_nodes.append(dist2_locator)
    else:
        pass
    
    if cmds.objExists(loc_grp):
        disconnect_nodes.append(loc_grp)
        
    cmds.delete(disconnect_nodes)    
    


'''--- Utils specific to autoRotate. ---'''


def baseLocators(geo):
    '''Locators for wheel measurements.'''
    name = '{}_{}'.format(utils.side(geo), utils.description(geo))

    dist1_locator = utils.createLocator('{}_wheelDist01_LOC'.format(name), 
                                        0, 0, 0)
    dist2_locator = utils.createLocator('{}_wheelDist02_LOC'.format(name), 
                                        0, 0, 0)
    center_locator = utils.createLocator('{}_wheelCenter_LOC'.format(name), 
                                        0, 0, 0)
    distance_grp = cmds.group(center_locator, dist1_locator, dist2_locator, 
                              name='{}_locs_GRP'.format(name))

    cmds.move(0, 0, 1, dist1_locator)
    cmds.move(0, 0, -1, dist2_locator)

    cmds.parentConstraint(dist1_locator, dist2_locator, center_locator)
    cmds.select(clear=True)

    dist1 = cmds.xform(dist1_locator, query=True, translation=True)
    dist2 = cmds.xform(dist2_locator, query=True, translation=True)

    # returns points in space (as locators) to be used in measureWheelDistance()
    return (dist1_locator, dist2_locator, center_locator, dist1, dist2, distance_grp)


def measureWheelDistance(wheel, dist1, dist2):
    '''Distance node to find wheel diameter.'''
    name = '{}_{}_DIST'.format(utils.side(wheel), utils.description(wheel))

    distance = cmds.distanceDimension(startPoint=dist1, endPoint=dist2)
    distance = cmds.rename('distanceDimension1', name)

    # returns dynamic distance node, driven by baseLocators()
    return distance
        

def autoRotateGrp(wheel):
    '''Group node that contains autoRotate expression and constraints.'''
    name = '{}_{}_{}'.format(utils.side(wheel), utils.description(wheel), 'autoRotate_GRP')
    
    cmds.select(clear=True)
    grp = cmds.group(wheel, name=name)

    cmds.xform(grp, centerPivots=True)

    # returns group to be driven by connections to achieve automatic rotation
    return grp


def autoRotateCtrl(locator, auto_rotate_ctrl):
    '''Main control in the system that controls automatic or manual wheel rotation.'''
    name = '{}_{}_{}'.format(utils.side(auto_rotate_ctrl), utils.description(auto_rotate_ctrl), 'autoRotate_CTRL')

    auto_rotate_ctrl = cmds.circle(name=name)
    cmds.delete(cmds.parentConstraint(locator, auto_rotate_ctrl))

    inputs = cmds.listHistory(auto_rotate_ctrl)
    normal_x = str('{}.normalX').format(inputs[1])
    cmds.setAttr(normal_x, 90)

    # returns ctrl that drives the autoRotate grp
    return auto_rotate_ctrl


def offsetCtrl(auto_rotate_ctrl, offset_ctrl):
    '''Creates offset control which drives wheel for offset rotation values.'''
    name = '{}_{}_{}'.format(utils.side(offset_ctrl), utils.description(offset_ctrl), 'offset_CTRL')

    offset_ctrl = cmds.circle(name=name)
    inputs = cmds.listHistory(offset_ctrl)
    wheel_radius = '{}.radius'.format(inputs[1])
    normal_x = '{}.normalX'.format(inputs[1])
    center_x = '{}.centerX'.format(inputs[1])
    center_z = '{}.centerZ'.format(inputs[1])

    utils.snap(auto_rotate_ctrl, offset_ctrl)

    cmds.setAttr(normal_x, 90)
    cmds.setAttr(wheel_radius, 0.6)
    
    if utils.side(offset_ctrl) == 'l':
        cmds.setAttr(center_x, 1)
    elif utils.side(offset_ctrl) == 'r':
        cmds.setAttr(center_x, -1)
        

    # returns control that allows for offset, evaluated after initial rotation
    return offset_ctrl


def wheelOrientGrp(wheel):
    '''Group node that controls proper rotation of auto wheel rot grp.'''
    name = '{}_{}_{}'.format(utils.side(wheel), utils.description(wheel), '_arOrient_GRP')

    grp = cmds.group(name=name)

    # returns group that will control the rotations Y and Z of autoRotate grp
    return grp


def wheelExpression(target, auto, offset, dist, wheel):
    '''Math that controls how the wheel will procedurally rotate.

    Args:
        target: object to apply expression to
        auto: object with an 'Auto' attribute, which toggles automatic rotation
        offset: object with an 'Offset' attibute, which offsets the current wheel rotation
        dist: distance node that measures the wheel's diameter
        wheel: object that represents the wheel

    Returns:
        str: expression with math to achieve automatic rotation based on diameter   
    '''
    
    name = '{}_{}_autoRotate_EXP'.format(utils.side(wheel), utils.description(wheel))

    string = textwrap.dedent('''
        if ({0}.auto == 1 ) {{
            $diff = {1}.translateZ - {1}.offset;
            {1}.rotateX -= $diff * -360 / ({2}.distance*3.14);
        }};
        {1}.offset = {1}.translateZ;'''.format(auto, offset, dist))

    expression = cmds.expression(name=name, object=target, string=string, alwaysEvaluate=True)

    return expression
    
    
# def wheelExpression(target, auto, offset, dist, wheel):
#     '''Math that controls how the wheel will procedurally rotate.'''
#     name = '{}_{}_{}'.format(utils.side(wheel), utils.description(wheel), 'autoRotate_EXP')

#     string = "  if (%s.auto == 1 ) {                                  \
#                     $diff = %s.translateZ - %s.offset ;               \
#                     %s.rotateX -= $diff * -360 / (%s.distance*3.14);  \
#                 };                                                    \
#                 %s.offset = %s.translateZ ; " % (auto, offset, offset, offset, dist, offset, offset)

#     expression = cmds.expression(name=name, object=target, string=string, alwaysEvaluate=True)

#     # returns expression with math to achieve automatic rotation based on diameter
#     return expression
    
    
def checkForAutoRotateBase(target):
    '''Check selection for base setup by finding initial distance node.'''
    distance_node = '{}_{}_DIST'.format(utils.side(target), utils.description(target))
    
    if cmds.objExists(distance_node):
        return True
    else:
        return False


def checkForAutoRotateConnections(target):
    '''Check selection for expression node driving auto rotation system.'''
    expression = '{}_{}_autoRotate_EXP'.format(utils.side(target), utils.description(target))
    
    if cmds.objExists(expression):
        return True
    else:
        return False