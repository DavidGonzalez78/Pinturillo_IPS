import streamlit as st
from partida import Partida
from streamlit_drawable_canvas import st_canvas
from datetime import datetime
from quotegenerator import QuoteGenerator

# Esto solo se hace una vez, al principio. Además, es global para todos los ordenadores que se conecten
@st.cache_resource
def generate_null_partidas_list():
    return []
partidas:list[Partida] = generate_null_partidas_list()


@st.cache_resource
def get_quote_generator():
    return QuoteGenerator()
quote_generator = get_quote_generator()





# Esta variable es propia de cada ordenador/usuario, y describe la fase en la que están jugando (seleccionar partida, dibujar, adivinar)
if not "user_phase" in st.session_state: st.session_state.user_phase = "Select partida"
if not "user_name" in st.session_state: st.session_state.user_name = ""
if not "user_partida" in st.session_state: st.session_state.user_partida = None
if not "show_drawing_quote" in st.session_state: st.session_state.show_drawing_quote = True



st.title("Joc d'endevinar dibuixets") 
st.session_state.user_name = st.text_input("Introdueix el teu nom")
st.write(f"Jugant com a {st.session_state.user_name} a la partida {st.session_state.user_partida} a la fase {st.session_state.user_phase} ")
st.divider()



if st.session_state.user_name:  

    if st.session_state.user_phase == "Select partida": 
        
        st.header("Selecciona la partida")
        col1, col2, col3 = st.columns(3)

        with col1: 
            if st.button("Crear partida"): 
                partidas.append(Partida(quote_generator))
        
        with col2: 
            if st.button("Refrescar"): 
                st.rerun(scope = "app")
        
        with col3: 
            if st.button("Guardar partides (no funciona)"): 
                for i, partida in enumerate(partidas): 
                    partida.save(save_dir = "partidas_guardadas", index = i)

        st.write("Partides disponibles: ")

        for i, partida in enumerate(partidas): # Por cada partida abierta, colocas un objeto que la representa (como un botón para unirte)

            phase = partida.phase
            blocked = partida.blocked
            player1, player2 = partida.player1, partida.player2
            
            # Botó per entrar a una partida i dibuixar
            if phase == "Make drawing" and not blocked: 
                text = f"{i+1}. Partida sense començar. Fes un dibuix! "
                if st.button(text): 
                    st.session_state.user_phase = "Drawing"
                    st.session_state.user_partida = partida
                    st.session_state.user_partida.player1 = st.session_state.user_name
                    st.session_state.user_partida.block()
                    st.rerun()
            
            # Botó per entrar a una partida i endevinar
            if phase == "Make guess" and not blocked: 
                text = f"{i+1}. Partida començada, amb dibuix fet per {player1}. Endevina!"
                if st.button(text): 
                    if player1 != st.session_state.user_name: 
                        st.session_state.user_phase = "Guessing"
                        st.session_state.user_partida = partida
                        st.session_state.user_partida.player2 = st.session_state.user_name
                        st.session_state.user_partida.block()
                        st.rerun()
                    else: 
                        st.write("Ja has jugat en aquesta partida! Li toca a un altre.")
            
            # Botons per a partides bloquejades o acabades
            if phase == "Make drawing" and blocked: 
                text = f"{i+1}. Partida començada, {player1} està dibuixant (no pots entrar)"
                st.warning(text)
            
            if phase == "Make guess" and blocked: 
                text = f"{i+1}. Partida començada, {player2} està endevinant (no pots entrar)"
                st.warning(text)

            if phase == "Finished": 
                if partida.ending == "won": text = f"{i+1}. Partida acabada entre {player1} i {player2} amb {len(partida.guessed_quotes)} intents"
                else: text = f"{i+1}. Partida acabada entre {player1} i {player2}, i {player2} s'ha rendit"
                st.info(text)

        
        st.divider()
        if st.button("Veure partides anteriors..."): 

            for i, partida in enumerate(partidas): # Por cada partida abierta, colocas un objeto que la representa (como un botón para unirte)

                phase = partida.phase
                ending = partida.ending
                player1, player2 = partida.player1, partida.player2

                if phase == "Finished": 
                    t = "(i ho va aconseguir)" if ending=="won" else "(però no ho va aconseguir)"
                    st.subheader(f"Partida {i}, on {player1} va dibuixar i {player2} va endevinar " + t )
                    st.warning(f"Text: {partida.quote}")
                    st.image(  partida.drawing.image_data  )
                    st.dataframe(partida.guessed_quotes)




    if st.session_state.user_phase == "Drawing": 

        st.header("Etapa de dibuixar")

        col1, col2 = st.columns(2)

        with col1: 
            st.write("Has de dibuixar el següent: ")

        with col2: 
            st.session_state.show_drawing_quote = not st.checkbox("Ocultar text")
        
        if st.session_state.show_drawing_quote:
            st.warning( '"""' + st.session_state.user_partida.quote + '"""' )
        else: 
            st.warning( '[Text ocult]' )
        

        canvas = st_canvas(
            fill_color="white",
            stroke_width=3,
            stroke_color="black",
            height=300,
            drawing_mode="freedraw",
            background_color="white",
        )

        col1, col2 = st.columns(2)

        with col1: 
            if st.button("Enviar"): 
                st.session_state.user_partida.play_drawing(st.session_state.user_name, canvas)
                st.session_state.user_partida.unblock()
                st.session_state.user_phase = "Select partida"
                st.rerun()
        
        with col2: 
            if st.button("Sortir"): 
                st.session_state.user_partida.unblock()
                st.session_state.user_phase = "Select partida"
                st.rerun()
            



    if st.session_state.user_phase == "Guessing": 

        st.header("Endevina el dibuix! ")
        st.write("Has d'endevinar què és el següent dibuix: ")
        st.image(  st.session_state.user_partida.drawing.image_data  )

        guessed_quote = st.text_input("Introdueix la teva proposta: ")

        show_solucio = False
        col1, col2, col3 = st.columns(3)

        with col1: 
            if st.button("Enviar proposta"): 
                won, scores = st.session_state.user_partida.guess_drawing(st.session_state.user_name, guessed_quote)
                
                if won: 
                    st.session_state.user_partida.unblock()
                    st.session_state.user_phase = "Select partida"
                    st.rerun()
                    

        with col2: 
            if st.button("Sortir"): 
                st.session_state.user_partida.unblock()
                st.session_state.user_phase = "Select partida"
                st.rerun()
        

        with col3: 
            if len(st.session_state.user_partida.guessed_quotes) <= 30:
                pass
            else: 
                if st.button("Veure solució"): 
                    show_solucio = True
        
        if show_solucio: 
            st.warning(f"La solució és: {st.session_state.user_partida.quote}")              
        

        if len(st.session_state.user_partida.guessed_quotes) > 0:
            st.write("Thas equivocat, aqui pots veure els teus errors i els intents anteriors: ")
            st.dataframe(st.session_state.user_partida.guessed_quotes)
        

        explicacio_metriques = [
            "- **Common words similarity:** És proporció de paraules del quote real que has trobat. ",
            "- **Semantic similarity:** Mesura la similitud en el significat semàntic, utilitza word-embeddings. ",
            "- **Phonetic similarity:** Mesura la similitud en la pronunciació i fonètica. ",
            "- **Levenstein:** Calcula la mínima quantitat d'operaciones que cal fer al text per transformar-lo al real. ",
            "- **Total_score:** És la mitjana entre les quatre mesures anteriors.",
        ]
        if st.button("Què es cada mètrica? "): 
            for text in explicacio_metriques: 
                st.write(text)

        








# "Choose quote", "Make drawing", "Make guess", "Finished"