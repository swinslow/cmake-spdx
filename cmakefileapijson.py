# SPDX-License-Identifier: Apache-2.0

import json
import os

import cmakefileapi

def parseReply(replyIndexPath):
    replyDir, replyIndexFilename = os.path.split(replyIndexPath)

    # first we need to find the codemodel reply file
    try:
        with open(replyIndexPath, 'r') as indexFile:
            js = json.load(indexFile)

            # get reply object
            reply_dict = js.get("reply", {})
            if reply_dict == {}:
                print(f"no \"reply\" field found in index file")
                return None
            # get codemodel object
            cm_dict = reply_dict.get("codemodel-v2", {})
            if cm_dict == {}:
                print(f"no \"codemodel-v2\" field found in \"reply\" object in index file")
                return None
            # and get codemodel filename
            jsonFile = cm_dict.get("jsonFile", "")
            if jsonFile == "":
                print(f"no \"jsonFile\" field found in \"codemodel-v2\" object in index file")
                return None

            return parseCodemodel(replyDir, jsonFile)

    except OSError as e:
        print(f"Error loading {replyIndexPath}: {str(e)}")
        return None
    except json.decoder.JSONDecodeError as e:
        print(f"Error parsing JSON in {replyIndexPath}: {str(e)}")
        return None

def parseCodemodel(replyDir, codemodelFile):
    codemodelPath = os.path.join(replyDir, codemodelFile)

    try:
        with open(codemodelPath, 'r') as cmFile:
            js = json.load(cmFile)

            cm = cmakefileapi.Codemodel()

            # FIXME for correctness, should probably check kind and version

            # get paths
            paths_dict = js.get("paths", {})
            cm.paths_source = paths_dict.get("source", "")
            cm.paths_build = paths_dict.get("build", "")

            # get configurations
            configs_arr = js.get("configurations", [])
            for cfg_dict in configs_arr:
                cfg = parseConfig(cfg_dict, replyDir)
                if cfg:
                    cm.configurations.append(cfg)

            return cm

    except OSError as e:
        print(f"Error loading {replyIndexPath}: {str(e)}")
        return None
    except json.decoder.JSONDecodeError as e:
        print(f"Error parsing JSON in {replyIndexPath}: {str(e)}")
        return None

def parseConfig(cfg_dict, replyDir):
    cfg = cmakefileapi.Config()
    cfg.name = cfg_dict.get("name", "")

    # parse and add each directory
    dirs_arr = cfg_dict.get("directories", [])
    for dir_dict in dirs_arr:
        if dir_dict != {}:
            cfgdir = cmakefileapi.ConfigDir()
            cfgdir.source = dir_dict.get("source", "")
            cfgdir.build = dir_dict.get("build", "")
            cfgdir.parentIndex = dir_dict.get("parentIndex", -1)
            cfgdir.childIndexes = dir_dict.get("childIndexes", [])
            cfgdir.projectIndex = dir_dict.get("projecttIndex", -1)
            cfgdir.targetIndexes = dir_dict.get("targetIndexes", [])
            minCMakeVer_dict = dir_dict.get("minimumCMakeVersion", {})
            cfgdir.minimumCMakeVersion = minCMakeVer_dict.get("string", "")
            cfgdir.hasInstallRule = dir_dict.get("hasInstallRule", False)
            cfg.directories.append(cfgdir)

    # parse and add each project
    projects_arr = cfg_dict.get("projects", [])
    for prj_dict in projects_arr:
        if prj_dict != {}:
            prj = cmakefileapi.ConfigProject()
            prj.name = prj_dict.get("name", "")
            prj.parentIndex = prj_dict.get("parentIndex", -1)
            prj.childIndexes = prj_dict.get("childIndexes", [])
            prj.directoryIndexes = prj_dict.get("directoryIndexes", [])
            prj.targetIndexes = prj_dict.get("targetIndexes", [])
            cfg.projects.append(prj)

    # parse and add each target
    cfgTargets_arr = cfg_dict.get("targets", [])
    for cfgTarget_dict in cfgTargets_arr:
        if cfgTarget_dict != {}:
            cfgTarget = cmakefileapi.ConfigTarget()
            cfgTarget.name = cfgTarget_dict.get("name", "")
            cfgTarget.id = cfgTarget_dict.get("id", "")
            cfgTarget.directoryIndex = cfgTarget_dict.get("directoryIndex", -1)
            cfgTarget.projectIndex = cfgTarget_dict.get("projectIndex", -1)
            cfgTarget.jsonFile = cfgTarget_dict.get("jsonFile", "")

            if cfgTarget.jsonFile != "":
                cfgTarget.target = parseTarget(os.path.join(replyDir, cfgTarget.jsonFile))
            else:
                cfgTarget.target = None

            cfg.configTargets.append(cfgTarget)

    return cfg

def parseTarget(targetPath):
    try:
        with open(targetPath, 'r') as targetFile:
            js = json.load(targetFile)

            target = cmakefileapi.Target()

            target.name = js.get("name", "")
            target.id = js.get("id", "")
            target.type = parseTargetType(js.get("type", "UNKNOWN"))
            target.backtrace = js.get("backtrace", -1)
            target.folder = js.get("folder", "")

            # get paths
            paths_dict = js.get("paths", {})
            target.paths_source = paths_dict.get("source", "")
            target.paths_build = paths_dict.get("build", "")

            target.nameOnDisk = js.get("nameOnDisk", "")

            # parse artifacts if present
            artifacts_arr = js.get("artifacts", [])
            target.artifacts = []
            for artifact_dict in artifacts_arr:
                artifact_path = artifact_dict.get("path", "")
                if artifact_path != "":
                    target.artifacts.append(artifact_path)

            target.isGeneratorProvided = js.get("isGeneratorProvided", False)

            # call separate functions to parse subsections
            parseTargetInstall(target, js)
            parseTargetLink(target, js)
            parseTargetArchive(target, js)
            parseTargetDependencies(target, js)
            parseTargetSources(target, js)
            parseTargetSourceGroups(target, js)
            parseTargetCompileGroups(target, js)
            parseTargetBacktraceGraph(target, js)

            return target

    except OSError as e:
        print(f"Error loading {replyIndexPath}: {str(e)}")
        return None
    except json.decoder.JSONDecodeError as e:
        print(f"Error parsing JSON in {replyIndexPath}: {str(e)}")
        return None

def parseTargetType(targetType):
    if targetType == "EXECUTABLE":
        return cmakefileapi.TargetType.EXECUTABLE
    elif targetType == "STATIC_LIBRARY":
        return cmakefileapi.TargetType.STATIC_LIBRARY
    elif targetType == "SHARED_LIBRARY":
        return cmakefileapi.TargetType.SHARED_LIBRARY
    elif targetType == "MODULE_LIBRARY":
        return cmakefileapi.TargetType.MODULE_LIBRARY
    elif targetType == "OBJECT_LIBRARY":
        return cmakefileapi.TargetType.OBJECT_LIBRARY
    elif targetType == "UTILITY":
        return cmakefileapi.TargetType.UTILITY
    else:
        return cmakefileapi.TargetType.UNKNOWN

def parseTargetInstall(target, js):
    install_dict = js.get("install", {})
    if install_dict == {}:
        return
    prefix_dict = install_dict.get("prefix", {})
    target.install_prefix = prefix_dict.get("path", "")

    destinations_arr = install_dict.get("destinations", [])
    for destination_dict in destinations_arr:
        dest = cmakefileapi.TargetInstallDestination()
        dest.path = destination_dict.get("path", "")
        dest.backtrace = destination_dict.get("backtrace", -1)
        target.install_destinations.append(dest)

def parseTargetLink(target, js):
    link_dict = js.get("link", {})
    if link_dict == {}:
        return
    target.link_language = link_dict.get("language", {})
    target.link_lto = link_dict.get("lto", False)
    sysroot_dict = link_dict.get("sysroot", {})
    target.link_sysroot = sysroot_dict.get("path", "")

    fragments_arr = link_dict.get("commandFragments", [])
    for fragment_dict in fragments_arr:
        fragment = cmakefileapi.TargetCommandFragment()
        fragment.fragment = fragment_dict.get("fragment", "")
        fragment.role = fragment_dict.get("role", "")
        target.link_commandFragments.append(fragment)

def parseTargetArchive(target, js):
    archive_dict = js.get("archive", {})
    if archive_dict == {}:
        return
    target.archive_lto = archive_dict.get("lto", False)
 
    fragments_arr = archive_dict.get("commandFragments", [])
    for fragment_dict in fragments_arr:
        fragment = cmakefileapi.TargetCommandFragment()
        fragment.fragment = fragment_dict.get("fragment", "")
        fragment.role = fragment_dict.get("role", "")
        target.archive_commandFragments.append(fragment)

def parseTargetDependencies(target, js):
    dependencies_arr = js.get("dependencies", [])
    for dependency_dict in dependencies_arr:
        dep = cmakefileapi.TargetDependency()
        dep.id = dependency_dict.get("id", "")
        dep.backtrace = dependency_dict.get("backtrace", -1)
        target.dependencies.append(dep)

def parseTargetSources(target, js):
    sources_arr = js.get("sources", [])
    for source_dict in sources_arr:
        src = cmakefileapi.TargetSource()
        src.path = source_dict.get("path", "")
        src.compileGroupIndex = source_dict.get("compileGroupIndex", -1)
        src.sourceGroupIndex = source_dict.get("sourceGroupIndex", -1)
        src.isGenerated = source_dict.get("isGenerated", False)
        src.backtrace = source_dict.get("backtrace", -1)
        target.sources.append(src)

def parseTargetSourceGroups(target, js):
    sourceGroups_arr = js.get("sourceGroups", [])
    for sourceGroup_dict in sourceGroups_arr:
        srcgrp = cmakefileapi.TargetSourceGroup()
        srcgrp.name = sourceGroup_dict.get("name", "")
        srcgrp.sourceIndexes = sourceGroup_dict.get("sourceIndexes", [])
        target.sourceGroups.append(srcgrp)

def parseTargetCompileGroups(target, js):
    compileGroups_arr = js.get("compileGroups", [])
    for compileGroup_dict in compileGroups_arr:
        cmpgrp = cmakefileapi.TargetCompileGroup()
        cmpgrp.sourceIndexes = compileGroup_dict.get("sourceIndexes", [])
        cmpgrp.language = compileGroup_dict.get("language", "")
        cmpgrp.sysroot = compileGroup_dict.get("sysroot", "")

        commandFragments_arr = compileGroup_dict.get("compileCommandFragments", [])
        for commandFragment_dict in commandFragments_arr:
            fragment = commandFragment_dict.get("fragment", "")
            if fragment != "":
                cmpgrp.compileCommandFragments.append(fragment)

        includes_arr = compileGroup_dict.get("includes", [])
        for include_dict in includes_arr:
            grpInclude = cmakefileapi.TargetCompileGroupInclude()
            grpInclude.path = include_dict.get("path", "")
            grpInclude.isSystem = include_dict.get("isSystem", False)
            grpInclude.backtrace = include_dict.get("backtrace", -1)
            cmpgrp.includes.append(grpInclude)

        precompileHeaders_arr = compileGroup_dict.get("precompileHeaders", [])
        for precompileHeader_dict in precompileHeaders_arr:
            grpHeader = cmakefileapi.TargetCompileGroupPrecompileHeader()
            grpHeader.header = precompileHeader_dict.get("header", "")
            grpHeader.backtrace = precompileHeader_dict.get("backtrace", -1)
            cmpgrp.precompileHeaders.append(grpHeader)

        defines_arr = compileGroup_dict.get("defines", [])
        for define_dict in defines_arr:
            grpDefine = cmakefileapi.TargetCompileGroupDefine()
            grpDefine.define = define_dict.get("define", "")
            grpDefine.backtrace = define_dict.get("backtrace", -1)
            cmpgrp.defines.append(grpDefine)

        target.compileGroups.append(cmpgrp)

def parseTargetBacktraceGraph(target, js):
    backtraceGraph_dict = js.get("backtraceGraph", {})
    if backtraceGraph_dict == {}:
        return
    target.backtraceGraph_commands = backtraceGraph_dict.get("commands", [])
    target.backtraceGraph_files = backtraceGraph_dict.get("files", [])

    nodes_arr = backtraceGraph_dict.get("nodes", [])
    for node_dict in nodes_arr:
        node = cmakefileapi.TargetBacktraceGraphNode()
        node.file = node_dict.get("file", -1)
        node.line = node_dict.get("line", -1)
        node.command = node_dict.get("command", -1)
        node.parent = node_dict.get("parent", -1)
        target.backtraceGraph_nodes.append(node)
