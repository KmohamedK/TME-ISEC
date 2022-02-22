#include<stdio.h>
#include<stdlib.h>


int* multiplication (int* P1,int* P2, int d_p1, int d_p2){

    int  taille_p3 = d_p1 + d_p2+1; 
    int* P3 = malloc(taille_p3 * sizeof(int)); 

    for(int i =0 ; i < taille_p3; i++){
        P3[i] = 0; 
    }

    for (int i=0; i< d_p1+1 ;i++){
        for (int j=0; j< d_p2+1; j++){

            P3[i+j]+=(P1[i]* P2[j]);

        }

    }
    for (int i = 0; i < taille_p3+1; i++){
        printf("coef %d = %d \n", i, P3[i]); 
    }
    return P3;
}



int main(){
    int p1[3] = {0, 0, 1}; 
    int p2[3] = {0, 0, 1}; 
    printf("exemple 1 : \n Le calcul est (x**2)*(x**2) \n La reponse est x**4 \n"); 
    multiplication(p1, p2, 2, 2); 

    int p3[3] = {2, 1, 1}; // x**2 + x +2  
    int p4[3] = {1, 1, 0}; // x +1
    printf("exemple 2 : \n Le calcul est (x**2 + x + 2)*(x + 1) \n La reponse est  x**3 + 2 x**2 + 3 x + 2 \n"); 
    multiplication(p3, p4, 2, 2); // Le resultat est x**3 + 2 x**2 + 3 x + 2

    return 0; 
}