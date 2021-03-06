#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import pandas as pd
import trimesh as tm
import pyrender as pr
import os.path
from pathlib import Path
import open3d as o3d
import os 
import earthpy as et 

home_dict = et.io.HOME
desktop = os.path.join(et.io.HOME, 'Desktop')
target_dir = os.path.join(desktop, 'MR_Project')

#Check whether the directory exists 
if os.path.exists(target_dir) : 
    print('True')
else:
    print("Target directory does not exist, be sure where MR_Project file does exist")


#finding the scaling factor of all shapes to compute the correct area and volumes.
#this is applied because there are non-watertight meshes
def scale_factor(mesh):

    coords = tm.bounds.corners(mesh.bounds)
    diffx = (max(coords[:,0]) - min(coords[:,0]))
    diffy = (max(coords[:,1]) - min(coords[:,1]))
    diffz = (max(coords[:,2]) - min(coords[:,2]))
    
    s_factor = max(diffx, diffy, diffz)
    return s_factor


#import the original meshes and collect its statistics in a csv file
def mesh_import_export(input_directory, output_directory):
    my_meshlist = list()
    trimesh_list = list()
    class_list = list()
    df = pd.DataFrame()
    d = []
    
    #import 3d images and appen them to a list
    for filename1 in os.listdir(input_directory):
        class_name = str(filename1)
        current_path = "".join((input_directory, "/", filename1))
        i = 0
        for filename in os.listdir(current_path):
            if filename.endswith(".off") | filename.endswith(".ply"):
                loaded_trimesh = tm.load(current_path+"/"+filename)
                class_list += [class_name] 
                trimesh_list.append(loaded_trimesh)
                d.append({
                'Image File': filename,
                'Class': class_name,
                'Vertices': loaded_trimesh.vertices.shape[0],
                'Faces':    loaded_trimesh.faces.shape[0],
                'Shape':    loaded_trimesh.faces.shape[1],
                'Area': loaded_trimesh.area/(scale_factor(loaded_trimesh)**2),
                'Volume': loaded_trimesh.volume/(scale_factor(loaded_trimesh)**3),
                'Avarage Area per Face': loaded_trimesh.area/loaded_trimesh.faces.shape[0],
                'Min Facets Area': loaded_trimesh.facets_area.min(),
                'Max Facets Area' : loaded_trimesh.facets_area.max(),
                'Avarage Facets Area' : loaded_trimesh.facets_area.mean(),
                'Length of AABB': loaded_trimesh.extents[0],
                'Width of AABB': loaded_trimesh.extents[1],
                'Height of AABB': loaded_trimesh.extents[2],
                'Is volume': loaded_trimesh.is_volume,
                'Is watertight': loaded_trimesh.is_watertight})
                mesh = pr.Mesh.from_trimesh(loaded_trimesh, smooth = True)
                my_meshlist.append(mesh)
                i = i+1
                continue
            else:
                continue
    #append all of the lists together to create a csv file and export it
    df = pd.DataFrame(d)
    p = Path(output_directory)
    df.to_csv(Path(p, '3DImageInfo_before.csv'), index = False)
    print("The csv is created successfully.")


#initial preprocessing function for the original meshes
'''function for reading the files from a directory to resize the mesh and 
create summary info folder'''
def mesh_preprocess(input_directory, output_directory):
    
    path = output_directory + "/Updated_Offiles"
    if os.path.isdir(path) == False:
        os.mkdir(path)
    
    #import 3d images and appen them to a list
    for filename1 in os.listdir(input_directory):
        print(filename1)
        class_name = str(filename1)
        current_path = "".join((input_directory, "/", filename1))
  
        for filename in os.listdir(current_path):

            if filename.endswith(".off") | filename.endswith(".ply"):
                
                loaded_mesh = o3d.io.read_triangle_mesh(current_path+"/"+filename)
                faces = len(loaded_mesh.triangles)
               
                #if # of faces is below than 12000 or above than 16000, (1) read the file again with open3d,
                # (2) change the number of faces, (3) convert it again to off file and save in different directory, 
                #(4) then read it with trimesh again then save it dataframe

                if faces < 500: # or loaded_trimesh.faces.shape[0] < 1600:
                     
                     mesh_ref = loaded_mesh.subdivide_loop(number_of_iterations=2)
                     mesh_ref.remove_non_manifold_edges()
                     directory = path + '/'+ class_name + '_' + filename
                     o3d.io.write_triangle_mesh(directory, mesh_ref)
                     
                elif faces > 4000:
                    
                    mesh_smp = loaded_mesh.simplify_quadric_decimation(target_number_of_triangles=4000)
                    mesh_smp.remove_non_manifold_edges()
                    obj = path + '/'+ class_name + '_' + filename
                    o3d.io.write_triangle_mesh(obj, mesh_smp)
  
                else:
                    
                    path_d = path + '/'+ class_name + '_' + filename
                    o3d.io.write_triangle_mesh(path_d, loaded_mesh)  
            
            else:
                continue
    
    print('Files are remeshed/decimated.')


#to preprocess a single mesh that is uploaded to the program
def preprocess(mesh, filename, in_path):
    
    output_directory = target_dir + "/New_outputs"
    output_direct = output_directory + "/preprocessed_mesh"
    if os.path.isdir(output_direct) == False:
        os.mkdir(output_direct)
    
    loaded_mesh = o3d.io.read_triangle_mesh(in_path)
    faces = len(loaded_mesh.triangles)

    if faces < 500: # or loaded_trimesh.faces.shape[0] < 1600:
         
         mesh_ref = loaded_mesh.subdivide_loop(number_of_iterations=2)
         mesh_ref.remove_non_manifold_edges()
         directory = output_direct + '/' + filename
         o3d.io.write_triangle_mesh(directory, mesh_ref)
         return directory
         
    elif faces > 4000:
        
        mesh_smp = loaded_mesh.simplify_quadric_decimation(target_number_of_triangles=4000)
        mesh_smp.remove_non_manifold_edges()
        obj = output_direct + '/' + filename
        o3d.io.write_triangle_mesh(obj, mesh_smp)
        return obj
  
    else:       
        path_d = output_direct + '/' + filename
        o3d.io.write_triangle_mesh(path_d, loaded_mesh)
        return path_d


#the statistical information extraction function which exports the results after transformations as csv
def csv_extract(input_dir, output_dir, name):
    d = []
    for filename in os.listdir(input_dir):
        
        new_dir = input_dir + '/' + filename
        mesh = tm.load(new_dir)
        split_string = filename.split("_")
        class_name = split_string[0]
        file_name = split_string[1]
        d.append({
                'Image File': file_name,
                'Class': class_name,
                'Vertices': mesh.vertices.shape[0],
                'Faces':    mesh.faces.shape[0],
                'Shape':    mesh.faces.shape[1],
                'Area': mesh.area,
                'Volume': mesh.volume,
                'Avarage Area per Face': mesh.area/mesh.faces.shape[0],
                'Min Facets Area': mesh.facets_area.min(),
                'Max Facets Area' : mesh.facets_area.max(),
                'Avarage Facets Area' : mesh.facets_area.mean(),
                'Length of AABB': mesh.extents[0],
                'Width of AABB': mesh.extents[1],
                'Height of AABB': mesh.extents[2],
                'Is watertight': mesh.is_watertight, 
                'Is volume': mesh.is_volume,
                'Avarage Length of Edges': mesh.edges_unique_length.mean()})
    
    df = pd.DataFrame(d)
    p = Path(output_dir)
    df.to_csv(Path(p, name), index = False)
    print("The csv is created successfully.")
     

#files reading and importing function for the main function of step 1&2
def mesh_import(dir_name):
    my_meshlist = list()
    trimesh_list = list()
    
    i = 0
    for filename in os.listdir(dir_name):       
        if filename.endswith(".off") | filename.endswith(".ply"):
            loaded_trimesh = tm.load(dir_name+"/"+filename)
            trimesh_list.append(loaded_trimesh)
            mesh = pr.Mesh.from_trimesh(loaded_trimesh, smooth = True)
            my_meshlist.append(mesh)
            i = i+1
            continue
        else:
            continue
    return my_meshlist, trimesh_list


#the function that prints average info of the mesh dataframe
def mesh_info(df):
    min_facets_area = df["Min Facets Area"].mean()
    max_facets_area = df["Max Facets Area"].mean()
    avg_facets_area = df["Avarage Facets Area"].mean()
    avg_area_per_face = df["Avarage Area per Face"].mean()
    min_area_per_face = df["Avarage Area per Face"].min()
    max_area_per_face = df["Avarage Area per Face"].max()
    avg_area = df["Area"].mean()
    avg_vertix = df["Vertices"].mean()
    avg_face = df["Faces"].mean()
    min_vertix = df['Vertices'].min()
    max_vertix = df['Vertices'].max()
    min_face = df['Faces'].min()
    max_face = df['Faces'].max()
   
    print(f"Minimum facet area: {min_facets_area}")
    print(f"Maximum facet area: {max_facets_area}")
    print(f"Average facet area: {avg_facets_area}")
    print(f"Avarage area per face for all shapes : {avg_area_per_face}")
    print(f"min area per Face for all shapes: {min_area_per_face}")
    print(f"Max area per Face for all shapes: {max_area_per_face}")
    print(f"The average total area of the shapes: {avg_area}")
    print(f" Minimum number of vertices: {min_vertix},\n maximum nmber of vertices: {max_vertix},\n minimum number of faces: {min_face},\n maximum number of faces: {max_face}.")
    print(f"The average number of vertices are {int(round(avg_vertix, 0))}, and the average number of faces are {int(round(avg_face, 0))}.")


#plot a histogram to see the distribution of num. of vertices and faces
def histogram(dataframe):
    plot1 = dataframe.hist(column='Vertices', bins=25, grid=False)
    for ax in plot1.flatten():
        ax.set_xlabel("Number of vertices")
        ax.set_ylabel("Number of meshes")
    plot1

    plot2 = dataframe.hist(column='Faces', bins=25, grid=False)
    for ax in plot2.flatten():
        ax.set_xlabel("Number of faces")
        ax.set_ylabel("Number of meshes")
    plot2
    
    plot3 = dataframe.hist(column='Area', bins=25, grid=False)
    for ax in plot3.flatten():
        ax.set_xlabel("Summed area of faces")
        ax.set_ylabel("Number of meshes")
    plot3
    
    plot4 = dataframe.hist(column='Avarage Area per Face', bins=25, grid=False)
    for ax in plot4.flatten():
        ax.set_xlabel("Avarage area per face of the meshes")
        ax.set_ylabel("Number of meshes")
    plot4
    
    plot5 = dataframe.hist(column='Avarage Facets Area', bins=25, grid=False)
    for ax in plot5.flatten():
        ax.set_xlabel("Avarage Facets Area of the meshes")
        ax.set_ylabel("Number of meshes")
    plot5
    
    plot6 = dataframe.hist(column='Min Facets Area', bins=25, grid=False)
    for ax in plot6.flatten():
        ax.set_xlabel("Min Facet area of the meshes")
        ax.set_ylabel("Number of meshes")
    plot6
    
    plot7 = dataframe.hist(column='Max Facets Area', bins=25, grid=False)
    for ax in plot7.flatten():
        ax.set_xlabel("Max Facet area of the meshes")
        ax.set_ylabel("Number of meshes")
    plot7


#3D rendering function
def upload_mesh(mesh_name):
    #trimesh den pymesh e obj transformation ekle
    scene_u = pr.Scene(ambient_light=True)
    scene_u.add(mesh_name)
    #scene_u.add_geometry()
    pr.Viewer(scene_u, use_raymond_lighting=True)
    
    
def render_meshes(mesh_list, index):
    scene_u = pr.Scene(ambient_light=True)
    chosen_mesh = mesh_list[0][int(index)]
    scene_u.add(chosen_mesh)
    pr.Viewer(scene_u, use_raymond_lighting=True)
    
    
def render_mesh(loaded_trimesh):
    mesh = pr.Mesh.from_trimesh(loaded_trimesh, smooth = True)
    scene_u = pr.Scene(ambient_light=True)
    scene_u.add(mesh)
    pr.Viewer(scene_u, use_raymond_lighting=True)
    
def facet_hist(old_mesh, new_mesh):
    from matplotlib import pyplot
    
    x = [old_mesh.facets_area]
    y = [new_mesh.facets_area]
    
    pyplot.hist(x, alpha=0.5, label='old mesh')
    pyplot.hist(y, alpha=0.5, label='new mesh')
    pyplot.legend(loc='upper right')
    pyplot.xlabel('facet area')
    pyplot.ylabel('number of facets')
    pyplot.show()
    
    

#STEP 2 NORMALIZATION FUNCTION DEFINITIONS

#Find the barycenter of a mesh
def barycenter(mesh) :
    area = mesh.area
    S = 1/area
    i = 0
    loop_sum = 0 
    for row in mesh.faces:
        face_a = mesh.area_faces[i]
        face_a.astype(int)
        face_x = row[0]
        face_y = row[1]
        face_z = row[2]
        #norm calculation here
        vect = ((mesh.vertices[face_x] + mesh.vertices[face_y] + mesh.vertices[face_z])/3)
        trivertices = (len(mesh.vertices)* face_a * S)*vect
        loop_sum += trivertices
        i += 1 
    loop_ave = loop_sum/len(mesh.vertices)
    return loop_ave


#translation of the object to origin
def translate(mesh):
    new_vertix_list = list()
    center = mesh.centroid
    for vertix in mesh.vertices:
        row = vertix - center
        new_vertix_list.append(row)
    translated_mesh = tm.Trimesh(vertices = new_vertix_list, faces = mesh.faces)
    return translated_mesh

#Find the eigenvectors and eigenvalues from covariance matrix /bozuk
def coveigen(mesh): 
    import numpy as np 
    i = 0
    loop_sum = 0 
    mi = np.matrix(barycenter(mesh))
    for row in mesh.faces:
        face_a = mesh.area_faces[i]
        gi = np.matrix(mesh.triangles_center[i])
        diff = gi - mi
        transpose = np.transpose(diff)
        covrow = np.dot(transpose, diff)
        #print(covrow)
        loop_i = face_a * covrow 
        loop_sum += loop_i 
        i +=1 
    cov_matr = loop_sum / len(mesh.faces)
    eig_vals, eig_vecs = np.linalg.eig(cov_matr)
    
    # idx = eig_vals.argsort()[::-1]   
    # eig_vals = eig_vals[idx]
    # eig_vecs = eig_vecs[:,idx]
    return(cov_matr, eig_vals, eig_vecs)
    
#apply the changes on vertices using transformation matrices
def mat_calc(matrix, mesh):
     matrix_mesh = np.matrix(mesh.vertices)
     result = np.dot(matrix_mesh, matrix)
     new_mesh = tm.Trimesh(vertices = result, faces = mesh.faces)
     tm.repair.fix_normals(new_mesh)
     tm.repair.fix_inversion(new_mesh)
     return new_mesh

#find the rotation values for x y and z
def fx_cal(mesh):
    grand_sum = 0
    i = 0
    for face in mesh.faces: #0-m triangles
        for corner in face:
            xai = mesh.vertices[(mesh.faces[corner][0])][0]
            xbi = mesh.vertices[(mesh.faces[corner][1])][0]
            xci = mesh.vertices[(mesh.faces[corner][2])][0]
            sums = xai + xbi + xci
            row = (np.sign(sums) * mesh.area_faces[i] * ((sums/3)**2)) 
            grand_sum += row
        i+= 1
    fx = grand_sum/mesh.area
    return fx

def fy_cal(mesh):
    grand_sum = 0
    i = 0
    for face in mesh.faces: #0-m triangles
        for corner in face:
            xai = mesh.vertices[(mesh.faces[corner][0])][1]
            xbi = mesh.vertices[(mesh.faces[corner][1])][1]
            xci = mesh.vertices[(mesh.faces[corner][2])][1]
            sums = xai + xbi + xci
            row = (np.sign(sums) * mesh.area_faces[i] * ((sums/3)**2)) 
            grand_sum += row
        i+= 1
    fy = grand_sum/mesh.area
    return fy

def fz_cal(mesh):
    grand_sum = 0
    i = 0
    for face in mesh.faces: #0-m triangles
        for corner in face:
            xai = mesh.vertices[(mesh.faces[corner][0])][2]
            xbi = mesh.vertices[(mesh.faces[corner][1])][2]
            xci = mesh.vertices[(mesh.faces[corner][2])][2]
            sums = xai + xbi + xci
            row = (np.sign(sums) * mesh.area_faces[i] * ((sums/3)**2)) 
            grand_sum += row
        i+= 1
    fz = grand_sum/mesh.area
    return fz

#flipping matrix construction
def f_matrix(fx, fy, fz):
    matrix = np.zeros((3, 3), int)
    np.fill_diagonal(matrix, (np.sign(fx), np.sign(fy), np.sign(fz)))
    return matrix

     
#scaling for meshes
def scale(mesh):
    new_vertices = list()
    coords = tm.bounds.corners(mesh.bounds)
    diffx = (max(coords[:,0]) - min(coords[:,0]))
    diffy = (max(coords[:,1]) - min(coords[:,1]))
    diffz = (max(coords[:,2]) - min(coords[:,2]))
    
    s_factor = max(diffx, diffy, diffz)
    
    for vertix in mesh.vertices:
        new_vertix = vertix/s_factor
        new_vertices.append(new_vertix)
    
    s_mesh = tm.Trimesh(vertices = new_vertices, faces = mesh.faces)
    
    tm.repair.fix_normals(mesh)
    tm.repair.fix_inversion(mesh)
    tm.repair.fix_winding(mesh)
    tm.repair.fill_holes(mesh)
    mesh.remove_duplicate_faces()
    return s_mesh


#normalization pipeline step by step
def normalization(input_directory, output_directory):
    path = output_directory + "/Normalized_OFFiles"
    if os.path.isdir(path) == False:
        os.mkdir(path)
    
    for filename in os.listdir(input_directory):
        
        mesh = tm.load(input_directory + '/' + filename)
        
        tm.repair.fix_normals(mesh)
        tm.repair.fix_inversion(mesh)
        tm.repair.fix_winding(mesh)
        tm.repair.fill_holes(mesh)
        mesh.remove_duplicate_faces()
        
        #tranlaste the mesh to origin
        mesh_o = translate(mesh)

        #find the covariance matrix etc
        cov, e_val, e_vec = coveigen(mesh_o)

        #rotate the mesh with eigenvectors
        mesh_r = mat_calc(e_vec, mesh_o)
        
        mesh_r = fix_mesh(mesh_r)
    
        #flip the mesh with its flipping matrix
        fx = fx_cal(mesh_r)
        fy = fy_cal(mesh_r)
        fz = fz_cal(mesh_r)
        flipping_m = f_matrix(fx, fy, fz)
        
        flipped_mesh = mat_calc(flipping_m, mesh_r)
        
        #scaling the image to 1x1x1 cube
        scaled_mesh = scale(flipped_mesh)

        
        #export the new mesh
        export_path = path + '/' + filename
        scaled_mesh.export(export_path, file_type = 'off')
    print("All the meshes are normalized.")
    
#normalization for a single mesh uploaded to the program in GUI
def normalize(in_path):

    mesh = tm.load(in_path)
    
    tm.repair.fix_normals(mesh)
    tm.repair.fix_inversion(mesh)
    tm.repair.fix_winding(mesh)
    tm.repair.broken_faces(mesh)
    mesh.remove_duplicate_faces()
    
    #tranlaste the mesh to origin
    mesh_o = translate(mesh)

    #find the covariance matrix etc
    cov, e_val, e_vec = coveigen(mesh_o)

    #rotate the mesh with eigenvectors
    mesh_r = mat_calc(e_vec, mesh_o)
    
    #fix the rotation if there are any flaws
    mesh_r = fix_mesh(mesh_r)

    #flip the mesh with its flipping matrix
    fx = fx_cal(mesh_r)
    fy = fy_cal(mesh_r)
    fz = fz_cal(mesh_r)
    flipping_m = f_matrix(fx, fy, fz)
    
    flipped_mesh = mat_calc(flipping_m, mesh_r)
    
    #scaling the image to 1x1x1 cube
    scaled_mesh = scale(flipped_mesh)
        
    return scaled_mesh

#------------------------------------------------------------------
#orientation fixing functions for the shapes which could not be well oriented after notmalization.

#fixing the orientation of a single mesh, used for in normalization step and GUI
def fix_mesh(mesh):
    if mesh.extents[1] > mesh.extents[0]:
            z_rot = [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]
            mesh = mat_calc(z_rot, mesh)
    else:
        pass
    
    if mesh.extents[2] > mesh.extents[0]:
        y_rot = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]
        mesh = mat_calc(y_rot, mesh)
    else:
        pass
    
    if mesh.extents[2] > mesh.extents[1]:
        x_rot = [[1,0,0], [0,0,1], [0,-1,0]]
        mesh = mat_calc(x_rot, mesh)
    else:
        pass
    
    return mesh


'''Only if you want to collect an external output of fixed meshes 
apart from the normalized meshes'''
def fix_orientation(input_directory, output_directory):
    path = output_directory + "/Fixed_OFFiles"
    if os.path.isdir(path) == False:
        os.mkdir(path)
    
    for filename in os.listdir(input_directory):
        mesh = tm.load(input_directory + '/' + filename)
        #fix the rotation if the max len is longer than the on on X-axis
        if mesh.extents[1] > mesh.extents[0]:
            z_rot = [[0, 1, 0], [-1, 0, 0], [0, 0, 1]]
            mesh = mat_calc(z_rot, mesh)
        else:
            pass
        
        if mesh.extents[2] > mesh.extents[0]:
            y_rot = [[0, 0, -1], [0, 1, 0], [1, 0, 0]]
            mesh = mat_calc(y_rot, mesh)
        else:
            pass
        
        if mesh.extents[2] > mesh.extents[1]:
            x_rot = [[1,0,0], [0,0,1], [0,-1,0]]
            mesh = mat_calc(x_rot, mesh)
        else:
            pass
        #export the new mesh
        export_path = path + '/' + filename
        mesh.export(export_path, file_type = 'off')
