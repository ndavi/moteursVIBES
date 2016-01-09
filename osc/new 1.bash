#echo $(awk '{cnt=0 ; for(i=1; i<=NF; i++) {if($i != "") {cnt++}} {print ""cnt""}}') #FS=" " $1 -eq 4
if [ $(id -u) -ne 0 ] #Verifie si l'utilisateur est root
then
 echo "Vous n'êtes pas root"
else
	cat $1 | (while read user lastname userid grpid #Lecture par ligne du fichier texte
		          do
			if [ ${#userid} -eq 4 ] &&  [ ${#grpid} -eq 4 ] #Vérifie si il y a bien 4 champs et la longueur des 2 derniers champs
			then 
			  if (grep -w $userid /etc/passwd > /dev/null) #Verifie l'existence de l'utilisateur
			  then 
		          echo "Cet utilisateur existe déjà"
			  else
		      if (grep -w $grpid /etc/group > /dev/null) #Verifie l'existence du groupe
			      then
				user=`echo "$user" | tr "A-Z" "a-z"`
				lastname=`echo "$lastname" | tr "A-Z" "a-z"`
				creditentials=$user.$lastname
                if [ ${#creditentials} -le 32 ] # Vérifie la longueur du nom + prenom
			  	then 
				useradd -u$userid -g$grpid $user.$lastname
				else
				echo "Creditentals trop grands"
				fi
			    else
				echo "Le groupe n'existe pas"
			    fi
		          fi
			else
			    echo "Un des champ n'est pas correct"
			fi
			  done)
fi