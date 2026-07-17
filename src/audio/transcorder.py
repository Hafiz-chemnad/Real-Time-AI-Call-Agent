import wave
import audioop
import os

def pcm_to_mulaw(input_filepath: str, output_filepath: str) -> bool:
    """
    Standard PCM WAV ഓഡിയോ ഫയലിനെ mu-law ഫോർമാറ്റിലേക്ക് മാറ്റുന്നു.
    """
    try:
        # Section 1: ഇൻപുട്ട് ഫയൽ തുറക്കുന്നു
        with wave.open(input_filepath, 'rb') as pcm_file:
            # ഓഡിയോയുടെ അടിസ്ഥാന വിവരങ്ങൾ എടുക്കുന്നു
            params = pcm_file.getparams()
            frames = pcm_file.readframes(pcm_file.getnframes())
            sample_width = pcm_file.getsampwidth()
            
            # ഈ കോഡ് 16-bit ഓഡിയോയ്ക്ക് വേണ്ടി മാത്രമുള്ളതാണ്
            if sample_width != 2:
                print("Error: Input file must be 16-bit PCM WAV.")
                return False

        # Section 2: Core Logic - ഗണിതശാസ്ത്രപരമായി mu-law ലേക്ക് മാറ്റുന്നു
        # audioop ലൈബ്രറി ഉപയോഗിച്ച് വോളിയം കുറയാതെ സൈസ് ചുരുക്കുന്നു
        mulaw_frames = audioop.lin2ulaw(frames, sample_width)

        # Section 3: പുതിയ ഫയൽ ആയി സേവ് ചെയ്യുന്നു
        with wave.open(output_filepath, 'wb') as mulaw_file:
            # mu-law ഫോർമാറ്റിന്റെ കോഡ് 7 ആണ്. ബാക്കി കാര്യങ്ങൾ ഇൻപുട്ട് ഫയലിന്റേത് തന്നെ
            mulaw_file.setparams((params.nchannels, 1, params.framerate, len(mulaw_frames), 'ULAW', 'G.711 mu-law'))
            mulaw_file.writeframes(mulaw_frames)
            
        print(f"Success: File saved to {output_filepath}")
        return True # Section 3: Return Output (Success ആണോ എന്ന് അറിയിക്കുന്നു)

    except Exception as e:
        print(f"Error during transcoding: {e}")
        return False

        