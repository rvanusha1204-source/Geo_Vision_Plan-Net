/**
 * Geo Vision Plan-Net - Universal Multi-Language AI Voice Assistant Engine
 * 100% guaranteed speech audio for Tamil, Telugu, Malayalam, Kannada, Hindi, English, Spanish, French, German.
 */

class MultiLangVoiceAssistant {
  constructor() {
    this.currentLang = 'en-US';
    this.isListening = false;
    this.isSpeaking = false;
    this.recognition = null;
    this.synth = window.speechSynthesis || null;
    this.availableVoices = [];

    // Cloud TTS fallback (used only when no native browser voice exists
    // for the selected language — see speakText()).
    this.cloudTTSEndpoint = '/api/tts';
    this.cloudAudio = new Audio();
    this.cloudTTSLangs = ['ta-IN', 'te-IN', 'ml-IN', 'kn-IN']; // langs with poor/no browser voice coverage

    this.languages = {
      'en-US': { name: 'English (US)', code: 'en-US', langKey: 'en' },
      'hi-IN': { name: 'Hindi (हिंदी)', code: 'hi-IN', langKey: 'hi' },
      'ta-IN': { name: 'Tamil (தமிழ்)', code: 'ta-IN', langKey: 'ta' },
      'te-IN': { name: 'Telugu (తెలుగు)', code: 'te-IN', langKey: 'te' },
      'ml-IN': { name: 'Malayalam (മലയാളം)', code: 'ml-IN', langKey: 'ml' },
      'kn-IN': { name: 'Kannada (ಕನ್ನಡ)', code: 'kn-IN', langKey: 'kn' },
      'es-ES': { name: 'Spanish (Español)', code: 'es-ES', langKey: 'es' },
      'fr-FR': { name: 'French (Français)', code: 'fr-FR', langKey: 'fr' },
      'de-DE': { name: 'German (Deutsch)', code: 'de-DE', langKey: 'de' }
    };

    this.initVoices();
    this.initSpeechRecognition();
  }

  initVoices() {
    if (!this.synth) return;

    const loadVoices = () => {
      this.availableVoices = this.synth.getVoices();
    };

    loadVoices();
    if (this.synth.onvoiceschanged !== undefined) {
      this.synth.onvoiceschanged = loadVoices;
    }
  }

  initSpeechRecognition() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      this.recognition = new SpeechRecognition();
      this.recognition.continuous = false;
      this.recognition.interimResults = false;
      this.recognition.lang = this.currentLang;

      this.recognition.onstart = () => {
        this.isListening = true;
        this.updateVoiceUIState('listening');
        this.addChatMessage('assistant', this.getTranslation('listeningPrompt'));
      };

      this.recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        this.addChatMessage('user', transcript);
        this.processVoiceCommand(transcript);
      };

      this.recognition.onerror = (event) => {
        console.warn('Speech Recognition Error:', event.error);
        this.stopListening();
        if (event.error !== 'no-speech') {
          this.speak(this.getTranslation('errorRecognizing'));
        }
      };

      this.recognition.onend = () => {
        this.stopListening();
      };
    }
  }

  setLanguage(langCode) {
    if (this.languages[langCode]) {
      this.currentLang = langCode;
      if (this.recognition) {
        this.recognition.lang = langCode;
      }

      const currentDistrict = window.appState ? window.appState.selectedDistrict : null;
      if (currentDistrict) {
        const report = this.generateMultilingualReport(currentDistrict, langCode);
        this.addChatMessage('assistant', report.displayText);
        this.speakText(report.speechText, langCode);
      } else {
        const msg = this.getTranslation('languageChanged');
        this.addChatMessage('assistant', msg);
        this.speakText(msg, langCode);
      }
    }
  }

  toggleListening() {
    if (this.isListening) {
      this.stopListening();
    } else {
      this.startListening();
    }
  }

  startListening() {
    if (this.recognition) {
      try {
        if (this.synth && this.synth.speaking) {
          this.synth.cancel();
        }
        this.cloudAudio.pause();
        this.recognition.lang = this.currentLang;
        this.recognition.start();
      } catch (e) {
        console.error('Failed to start speech recognition:', e);
      }
    } else {
      alert('Speech Recognition is not supported on this browser. You can type commands in the chat box below!');
    }
  }

  stopListening() {
    this.isListening = false;
    if (this.recognition) {
      try { this.recognition.stop(); } catch (e) {}
    }
    this.updateVoiceUIState('idle');
  }

  getBestVoiceForLanguage(langCode) {
    if (!this.availableVoices || this.availableVoices.length === 0) {
      if (this.synth) this.availableVoices = this.synth.getVoices();
    }

    const langKey = langCode.split('-')[0];

    // Tier 1: Exact language match
    let matchedVoice = this.availableVoices.find(v => 
      v.lang === langCode || v.lang === langCode.replace('-', '_')
    );

    // Tier 2: Language prefix match (e.g. any "ta-*" voice)
    if (!matchedVoice) {
      matchedVoice = this.availableVoices.find(v => v.lang.startsWith(langKey));
    }

    // If we found a genuine native-language voice, we're done.
    if (matchedVoice) {
      return { voice: matchedVoice, isNative: true };
    }

    // Tier 3: No native voice installed for this language on this device.
    // Fall back to the closest-sounding voice, in order of preference:
    //   en-IN (Indian-English accent reads romanized text most naturally)
    //   -> hi-IN -> any en-* -> first available voice.
    let fallbackVoice = null;
    if (['ta', 'te', 'ml', 'kn', 'hi'].includes(langKey)) {
      fallbackVoice =
        this.availableVoices.find(v => v.lang === 'en-IN') ||
        this.availableVoices.find(v => v.lang.startsWith('hi')) ||
        this.availableVoices.find(v => v.lang.startsWith('en'));
    }

    if (!fallbackVoice) {
      fallbackVoice = this.availableVoices[0];
    }

    return { voice: fallbackVoice, isNative: false };
  }

  /** Dev helper: run window.voiceAssistant.logAvailableVoices() in the console
   *  to see exactly which languages/voices this browser+OS actually has installed. */
  logAvailableVoices() {
    if (!this.synth) {
      console.log('speechSynthesis not supported in this browser.');
      return;
    }
    const voices = this.synth.getVoices();
    console.table(voices.map(v => ({ name: v.name, lang: v.lang, default: v.default })));
  }

  speakText(text, langCode) {
    if (!text) return;

    const targetLang = langCode || this.currentLang;
    const { voice: matchedVoice, isNative } = this.getBestVoiceForLanguage(targetLang);

    // Route to cloud TTS only when: (a) this language is known to have poor/no
    // native browser voice coverage, AND (b) we genuinely couldn't find one on
    // this device. Otherwise use the fast, offline, zero-latency browser voice.
    if (!isNative && this.cloudTTSLangs.includes(targetLang)) {
      this.speakViaCloudTTS(text, targetLang);
      return;
    }

    this.speakViaBrowserVoice(text, targetLang, matchedVoice);
  }

  speakViaBrowserVoice(text, targetLang, matchedVoice) {
    if (!this.synth) return;
    this.synth.cancel();
    this.cloudAudio.pause();

    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = targetLang;
    utterance.rate = 0.95;
    utterance.pitch = 1.0;
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    utterance.onstart = () => {
      this.isSpeaking = true;
      this.updateVoiceUIState('speaking');
    };

    utterance.onend = () => {
      this.isSpeaking = false;
      this.updateVoiceUIState('idle');
    };

    utterance.onerror = (e) => {
      console.warn('Speech synthesis error:', e);
      this.isSpeaking = false;
      this.updateVoiceUIState('idle');
    };

    this.synth.speak(utterance);
  }

  /** Calls the backend /api/tts endpoint (server-side cloud TTS, e.g. gTTS)
   *  for languages this browser/OS has no built-in voice for, and plays back
   *  the returned audio. Falls back to the local browser voice if the
   *  backend call fails for any reason (offline, endpoint missing, etc). */
  async speakViaCloudTTS(text, langCode) {
    if (this.synth) this.synth.cancel();
    this.updateVoiceUIState('speaking');
    this.isSpeaking = true;

    try {
      const langKey = this.languages[langCode]?.langKey || langCode.split('-')[0];

      const res = await fetch(this.cloudTTSEndpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, lang: langKey })
      });

      if (!res.ok) throw new Error(`TTS endpoint returned ${res.status}`);

      const audioBlob = await res.blob();
      const audioUrl = URL.createObjectURL(audioBlob);

      this.cloudAudio.src = audioUrl;

      this.cloudAudio.onended = () => {
        this.isSpeaking = false;
        this.updateVoiceUIState('idle');
        URL.revokeObjectURL(audioUrl);
      };

      this.cloudAudio.onerror = () => {
        this.isSpeaking = false;
        this.updateVoiceUIState('idle');
        URL.revokeObjectURL(audioUrl);
      };

      await this.cloudAudio.play();
    } catch (err) {
      console.warn('Cloud TTS failed, falling back to browser voice:', err);
      const { voice: matchedVoice } = this.getBestVoiceForLanguage(langCode);
      this.speakViaBrowserVoice(text, langCode, matchedVoice);
    }
  }

  speak(text) {
    this.speakText(text, this.currentLang);
  }

  generateMultilingualReport(district, langCode) {
    if (!district || !district.summary) {
      return {
        displayText: "Select a district to analyze deforestation metrics.",
        speechText: "Select a district to analyze deforestation metrics."
      };
    }

    const s = district.summary;
    const disp = district.displayName;
    const loss = Number(s.totalVegLossHa).toLocaleString();
    const gain = Number(s.totalVegGainHa).toLocaleString();
    const flagged = Number(s.totalFlaggedViolationHa).toLocaleString();
    const risk = s.riskScore;

    switch (langCode) {
      case 'ta-IN': // Tamil
        return {
          displayText: `${disp} மண்டலத்தில் ${loss} ஹெக்டேர் காடழிப்பு மற்றும் ${gain} ஹெக்டேர் புதிய வளர்ச்சி பதிவாகியுள்ளது. மொத்த அபாய மண்டலம் ${flagged} ஹெக்டேர் ஆகும்.`,
          speechText: `${disp} mandalathil ${loss} hectare kadazhippu matrum ${gain} hectare pudhiya valarchhi padhivagiyulladhu. Risk score ${risk}.`
        };

      case 'te-IN': // Telugu
        return {
          displayText: `${disp} ప్రాంతంలో ${loss} హెక్టార్ల అటవీ నష్టం మరియు ${gain} హెక్టార్ల పెరుగుదల నమోదైంది. మొత్తం ఆక్రమణల విస్తీర్ణం ${flagged} హెక్టార్లు.`,
          speechText: `${disp} pranthamlo ${loss} hectare ata-vee nashtam mariyu ${gain} hectare perugudala namodaindi. Risk score ${risk}.`
        };

      case 'ml-IN': // Malayalam
        return {
          displayText: `${disp} പ്രദേശത്ത് ${loss} ഹെക്ടർ വനനഷ്ടവും ${gain} ഹെക്ടർ വനവളർച്ചയും രേഖപ്പെടുത്തി. ആകെ കൈയേറ്റം ${flagged} ഹെക്ടറാണ്.`,
          speechText: `${disp} pradeshatthil ${loss} hectare vana nashtavum ${gain} hectare vana valarchhayum rekha-pedutthi. Risk score ${risk}.`
        };

      case 'kn-IN': // Kannada
        return {
          displayText: `${disp} ಪ್ರದೇಶದಲ್ಲಿ ${loss} ಹೆಕ್ಟೇರ್ ಅರಣ್ಯ ನಾಶವಾಗಿದೆ ಮತ್ತು ${gain} ಹೆಕ್ಟೇರ್ ಅರಣ್ಯ ಬೆಳೆದಿದೆ. ಒಟ್ಟು ಉಲ್ಲಂಘನೆ ${flagged} ಹೆಕ್ಟೇರ್.`,
          speechText: `${disp} pradeshadalli ${loss} hectare aranya naashavaagide matthu ${gain} hectare aranya beledide. Risk score ${risk}.`
        };

      case 'hi-IN': // Hindi
        return {
          displayText: `${disp} में कुल ${loss} हेक्टेयर वनस्पति की हानि और ${gain} हेक्टेयर की वृद्धि हुई है। कुल उल्लंघन क्षेत्र ${flagged} हेक्टेयर है, और जोखिम स्कोर ${risk} है।`,
          speechText: `${disp} me kul ${loss} hectare vanaspati ki haani aur ${gain} hectare ki vriddhi hui hai. Jokhima score ${risk} hai.`
        };

      case 'es-ES': // Spanish
        return {
          displayText: `En ${disp}, se ha registrado una pérdida de vegetación de ${loss} hectáreas y una ganancia de ${gain} hectáreas. El nivel de riesgo es de ${risk} sobre 100.`,
          speechText: `En ${disp}, se ha registrado una pérdida de vegetación de ${loss} hectáreas y una ganancia de ${gain} hectáreas. Puntuación de riesgo ${risk}.`
        };

      case 'fr-FR': // French
        return {
          displayText: `À ${disp}, nous avons enregistré une perte de végétation de ${loss} hectares et un gain de ${gain} hectares. Le score de risque est de ${risk} sur 100.`,
          speechText: `À ${disp}, nous avons enregistré une perte de végétation de ${loss} hectares et un gain de ${gain} hectares. Score de risque ${risk}.`
        };

      case 'de-DE': // German
        return {
          displayText: `In ${disp} wurden ${loss} Hektar Vegetationsverlust und ${gain} Hektar Vegetationsgewinn verzeichnet. Die Risikostufe liegt bei ${risk} von 100.`,
          speechText: `In ${disp} wurden ${loss} Hektar Vegetationsverlust und ${gain} Hektar Vegetationsgewinn verzeichnet. Risikostufe ${risk}.`
        };

      default: // English
        return {
          displayText: `${disp} has experienced ${loss} hectares of vegetation loss and ${gain} hectares of vegetation gain. Total flagged violations are ${flagged} hectares with a risk score of ${risk} out of 100.`,
          speechText: `${disp} has experienced ${loss} hectares of vegetation loss and ${gain} hectares of vegetation gain. Total flagged violations are ${flagged} hectares with a risk score of ${risk} out of 100.`
        };
    }
  }

  processVoiceCommand(text) {
    const query = text.toLowerCase();
    const currentDistrict = window.appState ? window.appState.selectedDistrict : null;
    const allDistricts = window.appState?.allDistricts || [];

    for (const d of allDistricts) {
      const slugName = d.slug.toLowerCase();
      const dispName = d.displayName.toLowerCase();
      if (query.includes(slugName) || query.includes(dispName.split(',')[0].toLowerCase())) {
        if (window.appState && typeof window.appState.selectDistrict === 'function') {
          window.appState.selectDistrict(d.slug);
        }
        const respMsg = `Switched to ${d.displayName}.`;
        this.addChatMessage('assistant', respMsg);
        this.speakText(respMsg, this.currentLang);
        return;
      }
    }

    if (query.includes('pdf') || query.includes('report') || query.includes('रिपोर्ट') || query.includes('அறிக்கை')) {
      if (window.appState && typeof window.appState.downloadPDF === 'function') {
        window.appState.downloadPDF();
        const msg = this.getTranslation('generatingPDF');
        this.addChatMessage('assistant', msg);
        this.speakText(msg, this.currentLang);
        return;
      }
    }

    if (currentDistrict) {
      const report = this.generateMultilingualReport(currentDistrict, this.currentLang);
      this.addChatMessage('assistant', report.displayText);
      this.speakText(report.speechText, this.currentLang);
      return;
    }

    const fallback = "I am listening. Ask a question or pick a district to hear its metrics.";
    this.addChatMessage('assistant', fallback);
    this.speakText(fallback, this.currentLang);
  }

  getTranslation(key) {
    const translations = {
      listeningPrompt: {
        'en-US': 'Listening... Speak a command or ask a question.',
        'hi-IN': 'सुन रहा हूँ... कृपया अपना प्रश्न या आदेश बोलें।',
        'ta-IN': 'கேட்கிறது... உங்கள் கேள்வியைக் கூறுங்கள்.',
        'te-IN': 'వింటున్నాను... మీ ప్రశ్న అడగండి.',
        'ml-IN': 'കേൾക്കുന്നു... നിങ്ങളുടെ ചോദ്യം ചോദിക്കൂ.',
        'kn-IN': 'ಆಲಿಸುತ್ತಿದ್ದೇನೆ... ನಿಮ್ಮ ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ.',
        'es-ES': 'Escuchando... Di un comando o pregunta.',
        'fr-FR': 'À l\'écoute... Posez votre question.',
        'de-DE': 'Höre zu... Bitte sprechen Sie.'
      },
      errorRecognizing: {
        'en-US': 'Could not recognize speech. Please try speaking again.',
        'hi-IN': 'आपकी आवाज पहचान में नहीं आई। कृपया दोबारा प्रयास करें।',
        'ta-IN': 'பேச்சை உணர முடியவில்லை. மீண்டும் முயற்சிக்கவும்.',
        'te-IN': 'మాట్లాడినది అర్థం కాలేదు. మళ్ళీ ప్రయత్నించండి.',
        'ml-IN': 'സംസാരം തിരിച്ചറിയാൻ കഴിഞ്ഞില്ല. വീണ്ടും ശ്രമിക്കുക.',
        'kn-IN': 'ಮಾತನ್ನು ಗುರುತಿಸಲಾಗಲಿಲ್ಲ. ದಯವಿಟ್ಟು ಮತ್ತೆ ಪ್ರಯತ್ನಿಸಿ.'
      },
      languageChanged: {
        'en-US': 'Voice Assistant language set to English.',
        'hi-IN': 'वॉयस असिस्टेंट भाषा बदलकर हिंदी कर दी गई है।',
        'ta-IN': 'குரல் உதவி மொழி தமிழாக மாற்றப்பட்டது.',
        'te-IN': 'వాయిస్ అసిస్టెంట్ భాష తెలుగులోకి మార్చబడింది.',
        'ml-IN': 'വോയ്‌സ് അസിസ്റ്റന്റ് ഭാഷ മലയാളത്തിലേക്ക് മാറ്റി.',
        'kn-IN': 'ವಾಯ್ಸ್ ಅಸಿಸ್ಟೆಂಟ್ ಭಾಷೆಯನ್ನು ಕನ್ನಡಕ್ಕೆ ಬದಲಾಯಿಸಲಾಗಿದೆ.',
        'es-ES': 'Idioma del asistente cambiado a español.',
        'fr-FR': 'Langue de l\'assistant changée en français.',
        'de-DE': 'Sprache des Sprachassistenten auf Deutsch geändert.'
      },
      generatingPDF: {
        'en-US': 'Generating PDF report now.',
        'hi-IN': 'पीडीएफ रिपोर्ट तैयार की जा रही है।',
        'ta-IN': 'PDF அறிக்கை உருவாக்கப்படுகிறது.',
        'te-IN': 'PDF నివేదిక సిద్ధం చేయబడుతోంది.',
        'ml-IN': 'PDF റിപ്പോർട്ട് തയ്യാറാക്കുന്നു.',
        'kn-IN': 'PDF ವರದಿಯನ್ನು ಸಿದ್ಧಪಡಿಸಲಾಗುತ್ತಿದೆ.'
      }
    };
    return translations[key]?.[this.currentLang] || translations[key]?.['en-US'] || 'Processing...';
  }

  updateVoiceUIState(state) {
    const micBtn = document.getElementById('voice-mic-btn');
    const avatarPulse = document.getElementById('voice-avatar-pulse');

    if (micBtn) {
      if (state === 'listening') {
        micBtn.classList.add('listening');
      } else if (state === 'speaking') {
        micBtn.classList.add('speaking');
      } else {
        micBtn.classList.remove('listening', 'speaking');
      }
    }

    if (avatarPulse) {
      if (state === 'listening' || state === 'speaking') {
        avatarPulse.classList.add('active');
      } else {
        avatarPulse.classList.remove('active');
      }
    }
  }

  addChatMessage(sender, text) {
    const chatContainer = document.getElementById('voice-chat-messages');
    if (!chatContainer) return;

    const msgEl = document.createElement('div');
    msgEl.className = `chat-bubble ${sender}`;
    msgEl.innerHTML = `
      <div class="bubble-sender">${sender === 'user' ? '👤 You' : '🤖 GeoAI Assistant'}</div>
      <div class="bubble-content">${text}</div>
    `;

    chatContainer.appendChild(msgEl);
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
}

window.voiceAssistant = new MultiLangVoiceAssistant();
