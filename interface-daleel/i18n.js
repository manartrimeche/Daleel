const DaleelI18n = (() => {
  const STORAGE_KEY = 'daleel_ui_lang';
  const SUPPORTED = ['fr', 'ar', 'en'];
  const RTL = new Set(['ar']);

  const dict = {
    fr: {
      'lang.label': 'Langue',
      'lang.fr': 'Français',
      'lang.ar': 'العربية',
      'lang.en': 'English',
      'lang.current': 'Langue actuelle : {language}',
      'common.loading': 'Chargement...',
      'common.online': 'En ligne',
      'common.connected': 'Connecté',
      'common.offline': 'Hors ligne',
      'common.error': 'Erreur',
      'common.close': 'Fermer',
      'common.cancel': 'Annuler',
      'common.save': 'Enregistrer',
      'common.ignore': 'Ignorer',
      'common.search': 'Rechercher',
      'common.upload': 'Uploader',
      'common.create': 'Créer',
      'common.delete': 'Supprimer',
      'common.details': 'Détail',
      'common.back': 'Retour',
      'common.previous': 'Préc.',
      'common.next': 'Suiv.',
      'common.status': 'Statut',
      'common.actions': 'Actions',
      'common.language': 'Langue',
      'common.name': 'Nom',
      'common.email': 'Email',
      'common.role': 'Rôle',
      'common.type': 'Type',
      'common.title': 'Titre',
      'common.description': 'Description',
      'common.profile': 'Profil',
      'common.score': 'Score',
      'common.frequency': 'Fréquence',
      'common.evidence': 'Preuves',
      'common.effectiveness': 'Eff.',
      'common.risk': 'Risque',
      'common.justification': 'Justification',
      'common.owner': 'Owner',
      'common.due': 'Échéance',
      'common.priority': 'Priorité',
      'common.assigned': 'Assigné',
      'common.updated': 'MàJ',
      'common.createdAt': 'Créée le',
      'common.expires': 'Expire',
      'common.subscription': 'Abonnement',
      'common.subscriptionEnd': "Fin d'abonnement",
      'common.sector': 'Secteur',
      'common.size': 'Taille',
      'common.employees': 'Employés',
      'common.members': 'Membres',
      'common.file': 'Fichier',
      'common.analyzedType': 'Type analysé',
      'common.auto': 'Auto',
      'common.all': 'Tous',
      'common.allLanguages': 'Toutes langues',
      'common.french': 'Français',
      'common.arabic': 'Arabe',
      'common.english': 'Anglais',
      'common.page': 'Page',
      'common.total': 'total',
      'common.none': 'Aucun',
      'common.notAvailable': 'Non disponible',
      'common.yes': 'Oui',
      'common.no': 'Non',
      'common.continue': 'Continuer',
      'common.select': 'Sélectionner',
      'common.add': 'Ajouter',
      'common.send': 'Envoyer',
      'common.deactivate': 'Désactiver',
      'common.revoke': 'Révoquer',
      'common.noUsers': 'Aucun utilisateur.',
      'common.noOrganizations': 'Aucune entreprise.',
      'role.super_admin': 'Super Admin',
      'role.owner': 'Gérant',
      'role.admin': 'Admin',
      'role.member': 'Membre',
      'role.viewer': 'Lecteur',
      'status.active': 'Actif',
      'status.inactive': 'Inactif',
      'status.pending': 'En attente',
      'status.pending_approval': "En attente d'approbation",
      'status.ready': 'Prêt',
      'status.processing': 'En traitement',
      'status.completed': 'Terminé',
      'status.failed': 'Échec',
      'status.error': 'Erreur',
      'status.open': 'Ouvert',
      'status.in_progress': 'En cours',
      'status.under_review': 'En revue',
      'status.resolved': 'Résolu',
      'status.closed': 'Fermé',
      'status.cancelled': 'Annulé',
      'status.approved': 'Approuvé',
      'status.rejected': 'Rejeté',
      'status.expired': 'Expiré',
      'status.revoked': 'Révoqué',
      'status.draft': 'Brouillon',
      'status.published': 'Publié',
      'status.not_analyzed': 'Non analysé',
      'status.applied': 'Appliqué',
      'status.partial': 'Partiel',
      'status.covered': 'Couvert',
      'status.not_covered': 'Non couvert',
      'subscription.monthly': 'Mensuel',
      'subscription.annual': 'Annuel',
      'priority.critical': 'Critique',
      'priority.high': 'Haute',
      'priority.medium': 'Moyenne',
      'priority.low': 'Faible',
      'severity.observation': 'Observation',
      'severity.minor': 'Mineur',
      'severity.major': 'Majeur',
      'docRole.evidence': 'Preuve',
      'docRole.incoming_request': 'Demande reçue',
      'docRole.policy': 'Politique',
      'docRole.contract': 'Contrat',
      'docRole.authority_notice': 'Notification autorité',
      'docRole.other': 'Autre',

      'index.title': 'Daleel - دليل | Expert Juridique Tunisien',
      'index.meta.description': 'Assistant juridique intelligent spécialisé en droit tunisien. Posez vos questions en arabe, français ou anglais.',
      'index.brand.subtitle': 'Expert Juridique Tunisien',
      'index.newChat': 'Nouvelle discussion',
      'index.admin': 'Admin',
      'index.case': 'Dossier',
      'index.nav.chat': 'Chat',
      'index.welcome.title': 'Bienvenue dans Daleel',
      'index.welcome.body': 'Bonjour, je suis <strong>Daleel</strong> (دليل), votre conseiller juridique spécialisé en droit tunisien. Je vous accompagne dans la compréhension du <strong>Code du travail</strong>, du <strong>Code des sociétés commerciales</strong> et de la <strong>Loi 63-2004</strong> sur la protection des données personnelles. Décrivez-moi votre situation en <strong>arabe</strong>, en <strong>français</strong> ou en <strong>anglais</strong>.',
      'index.suggestion.1': "Quelles sont les conditions de création d'une société en Tunisie ?",
      'index.suggestion.2': "Quelles sont les obligations du gérant d'une SARL ?",
      'index.suggestion.3': 'Quels sont les droits du travailleur en cas de licenciement abusif ?',
      'index.suggestion.4': 'Comment protéger les données personnelles de mes clients ?',
      'index.history.offline': 'Serveur non disponible',
      'index.history.loginRequired': 'Connexion requise',
      'index.input.placeholder': 'Posez votre question juridique...',
      'index.input.hint': 'Appuyez sur Entrée pour envoyer',
      'index.send': 'Envoyer',
      'index.sources.used': '{count} source{plural} utilisée{plural}',
      'index.feedback.title': 'Proposer une correction',
      'index.feedback.placeholder': 'Collez ici la réponse corrigée...',
      'index.feedback.tooShort': 'La correction est trop courte.',
      'index.feedback.saving': 'Enregistrement...',
      'index.feedback.saved': 'Correction enregistrée.',
      'index.feedback.failed': "Échec de l'enregistrement.",
      'index.feedback.network': 'Erreur réseau.',
      'index.error.generic': 'Une erreur est survenue. Veuillez réessayer.',
      'index.error.api': "Impossible de joindre l'API. Vérifiez que le serveur est démarré et accessible.",
      'index.error.detail': 'Détail : {message}',
      'index.case.prompt': 'Titre du dossier de conformité :',
      'index.case.created': "Dossier créé : **{title}**\n\nVous pouvez le consulter dans l'admin : [Ouvrir le dossier](/admin)",
      'index.case.createError': 'Erreur lors de la création du dossier.',
      'index.case.network': 'Erreur de connexion.',

      'admin.title': 'Daleel Admin - Plateforme de Conformité',
      'admin.nav.principal': 'Principal',
      'admin.nav.dashboard': 'Tableau de bord',
      'admin.nav.documents': 'Documents',
      'admin.nav.compliance': 'Conformité',
      'admin.nav.amendments': 'Amendements',
      'admin.nav.history': 'Historique',
      'admin.nav.cases': 'Dossiers',
      'admin.nav.companyProfile': 'Profil entreprise',
      'admin.nav.users': 'Utilisateurs',
      'admin.nav.organizations': 'Entreprises',
      'admin.nav.userManagement': 'Gestion des utilisateurs',
      'admin.nav.actions': 'Actions',
      'admin.nav.notifications': 'Notifications',
      'admin.nav.administration': 'Administration',
      'admin.footer.chat': 'Chat',
      'admin.footer.logout': 'Déconnexion',
      'admin.dashboard.recentActivity': 'Activité récente',
      'admin.dashboard.noEvents': 'Aucun événement',
      'admin.dashboard.serverOffline': 'Serveur non disponible',
      'admin.dashboard.serverOfflineHint': 'Démarrez le backend pour voir les données du tableau de bord.',
      'admin.dashboard.vectorEngine': 'Moteur vectoriel',
      'admin.dashboard.actionCriticality': 'Criticité des actions',
      'admin.dashboard.questionsPerDay': 'Questions / jour (30j)',
      'admin.dashboard.avgSatisfaction': 'Satisfaction moyenne (30j)',
      'admin.dashboard.coverageByProfile': 'Couverture de conformité par profil',
      'admin.dashboard.notifications': 'Notifications',
      'admin.dashboard.noEvent': 'Aucun événement',
      'admin.dashboard.noNotification': 'Aucune notification',
      'admin.dashboard.laws': 'Lois',
      'admin.dashboard.requirements': 'Exigences',
      'admin.dashboard.profiles': 'Profils',
      'admin.dashboard.pendingSuffix': 'en attente',
      'admin.dashboard.withCriticality': 'avec criticité',
      'admin.documents.title': 'Documents',
      'admin.documents.inDatabase': '{count} document(s) dans la base',
      'admin.documents.file': 'Fichier',
      'admin.documents.type': 'Type',
      'admin.documents.pages': 'Pages',
      'admin.documents.chunks': 'Chunks',
      'admin.documents.classify': 'Classifier',
      'admin.documents.uploadHint': 'Cliquez ou glissez un fichier (PDF, DOCX, TXT)',
      'admin.laws.title': 'Lois & Articles',
      'admin.laws.create': 'Créer une loi',
      'admin.laws.code': 'Code',
      'admin.laws.name': 'Nom',
      'admin.laws.description': 'Description',
      'admin.laws.bilingual': 'Bilingue',
      'admin.laws.createButton': 'Créer la loi',
      'admin.laws.articles': 'Articles',
      'admin.laws.segment': 'Segmenter',
      'admin.laws.criticality': 'Criticité',
      'admin.search.qa': 'Q/R Juridique',
      'admin.search.userQuestion': 'Question utilisateur',
      'admin.search.askPlaceholder': 'Ex: Quelle est la solution pratique pour se conformer aux obligations de tenue des registres ?',
      'admin.search.autoMode': 'Mode auto (choix intelligent)',
      'admin.search.classicMode': 'Mode classique (/ask)',
      'admin.search.agenticMode': 'Mode agentic (/ask-agentic)',
      'admin.search.ask': 'Poser la question',
      'admin.search.compare': 'Comparer classique vs agentic',
      'admin.search.tip': 'Astuce: Ctrl+Entrée pour lancer rapidement.',
      'admin.search.semantic': 'Recherche sémantique',
      'admin.search.placeholder': 'Rechercher dans les documents juridiques... (FR, AR ou EN)',
      'admin.users.members': 'Membres',
      'admin.users.invite': 'Inviter',
      'admin.users.pendingInvites': 'Invitations en cours',
      'admin.users.email': 'Email',
      'admin.users.role': 'Rôle',
      'admin.users.lastLogin': 'Dernière connexion',
      'admin.users.active': 'Actif',
      'admin.users.inviteMember': 'Inviter un membre',
      'admin.users.noOrganization': 'Aucune entreprise associée à ce compte.',
      'admin.users.inviteSent': 'Invitation envoyée',
      'admin.users.roleUpdated': 'Rôle mis à jour',
      'admin.users.statusUpdated': 'Statut mis à jour',
      'admin.users.userDisabled': 'Utilisateur désactivé',
      'admin.users.invitationRevoked': 'Invitation révoquée',
      'admin.users.confirmDeactivate': 'Désactiver cet utilisateur ?',
      'admin.users.confirmRevoke': 'Révoquer cette invitation ?',
      'admin.organizations.title': 'Entreprises',
      'admin.administration.title': 'Administration',
      'admin.adminTabs.laws': 'Lois & Articles',
      'admin.adminTabs.cases': 'Dossiers',
      'admin.adminTabs.posture': 'Posture',
      'admin.adminTabs.assessments': 'Évaluations',
      'admin.adminTabs.controls': 'Contrôles',
      'admin.adminTabs.exceptions': 'Exceptions',
      'admin.adminTabs.audit': 'Audit log',
      'admin.adminTabs.search': 'Recherche',
      'admin.adminTabs.vectors': 'Vecteurs',
      'admin.cases.title': 'Dossiers de conformité',
      'admin.cases.new': 'Nouveau dossier',
      'admin.cases.allPriorities': 'Toutes prio',
      'admin.cases.confirmDelete': 'Supprimer ce dossier ?',
      'admin.cases.deleted': 'Dossier supprimé',
      'admin.amendments.title': 'Amendements - Mise à jour de documents',
      'admin.amendments.subtitle': "Uploadez une nouvelle version d'un document. Le système détecte automatiquement la loi cible, compare les articles et notifie les profils entreprise.",
      'admin.amendments.uploadTitle': 'Uploader un document amendé',
      'admin.amendments.uploadDescription': 'Le système détecte automatiquement la loi cible depuis le contenu du document, compare les articles et notifie les profils entreprise des changements.',
      'admin.amendments.documentLabel': 'Document (PDF ou DOCX)',
      'admin.amendments.dropPrefix': 'Glissez un fichier ici ou',
      'admin.amendments.browse': 'parcourir',
      'admin.amendments.compareUpdate': 'Comparer & Mettre à jour',
      'admin.history.title': 'Historique des conversations',
      'admin.history.allMembers': 'Tous les membres',
      'admin.history.user': 'Utilisateur',
      'admin.history.question': 'Question',
      'admin.history.answerPreview': 'Réponse (aperçu)',
      'admin.history.sources': 'Sources',
      'admin.history.date': 'Date',
      'admin.history.none': 'Aucune conversation enregistrée',
      'admin.company.info': "Informations de l'entreprise",
      'admin.company.statistics': 'Statistiques',

      'auth.title': 'Daleel - Connexion',
      'auth.subtitle': 'Plateforme de conformité juridique tunisienne',
      'auth.loginTab': 'Connexion',
      'auth.registerTab': 'Inscription',
      'auth.email': 'Email',
      'auth.workEmail': 'Email professionnel',
      'auth.password': 'Mot de passe',
      'auth.login': 'Se connecter',
      'auth.fullName': 'Nom complet',
      'auth.fullName.placeholder': 'Votre nom complet',
      'auth.password.placeholder': 'Votre mot de passe',
      'auth.password.minPlaceholder': 'Minimum 8 caractères',
      'auth.confirmPassword': 'Confirmer le mot de passe',
      'auth.confirmPassword.placeholder': 'Confirmez votre mot de passe',
      'auth.personalInfo': 'Informations personnelles',
      'auth.personalInfo.subtitle': 'Créez votre compte administrateur',
      'auth.sector.title': "Secteur d'activité",
      'auth.sector.subtitle': 'Sélectionnez le secteur de votre entreprise',
      'auth.company.title': 'Profil entreprise',
      'auth.company.subtitle': 'Complétez les informations de votre organisation',
      'auth.company.name': "Nom de l'entreprise",
      'auth.company.placeholder': 'Ex: TechnoTunisie SARL',
      'auth.subscription.type': "Type d'abonnement",
      'auth.size': 'Taille',
      'auth.employees': "Nombre d'employés",
      'auth.employees.placeholder': 'Ex: 50',
      'auth.jurisdiction': 'Juridiction',
      'auth.tunisia': 'Tunisie',
      'auth.createAccount': 'Créer mon compte',
      'auth.footer': 'Daleel v1.0 - Conformité juridique intelligente',
      'auth.error.required': 'Veuillez remplir tous les champs. Le mot de passe doit contenir au moins 8 caractères.',
      'auth.error.sector': "Veuillez sélectionner un secteur d'activité.",
      'auth.error.organization': 'Veuillez saisir le nom de votre entreprise.',
      'auth.error.passwordMismatch': 'Les mots de passe ne correspondent pas.',
      'auth.error.login': 'Email ou mot de passe incorrect',
      'auth.error.server': 'Erreur de connexion au serveur',
      'auth.error.register': "Erreur lors de l'inscription",
      'auth.registrationPending': "Votre inscription a été envoyée au super admin. Vous pourrez vous connecter après approbation.",
      'auth.loading.login': 'Connexion...',
      'auth.loading.register': 'Création...',
      'auth.sector.finance': 'Finance',
      'auth.sector.banque': 'Banque',
      'auth.sector.assurance': 'Assurance',
      'auth.sector.industrie': 'Industrie',
      'auth.sector.technologie': 'Technologie',
      'auth.sector.telecom': 'Télécom',
      'auth.sector.sante': 'Santé',
      'auth.sector.pharma': 'Pharma',
      'auth.sector.transport': 'Transport',
      'auth.sector.btp': 'BTP',
      'auth.sector.commerce': 'Commerce',
      'auth.sector.energie': 'Énergie',
      'auth.sector.education': 'Éducation',
      'auth.sector.agriculture': 'Agriculture',
      'auth.sector.tourisme': 'Tourisme',
      'auth.sector.services': 'Services',
      'auth.sector.immobilier': 'Immobilier',
      'auth.sector.autre': 'Autre',
      'auth.size.micro': 'Micro (1-9)',
      'auth.size.small': 'Petite (10-49)',
      'auth.size.medium': 'Moyenne (50-249)',
      'auth.size.large': 'Grande (250+)',

      'invite.title': 'Daleel - Invitation',
      'invite.subtitle': 'Vous avez été invité à rejoindre une organisation',
      'invite.loading': "Vérification de l'invitation...",
      'invite.expired.title': 'Invitation expirée',
      'invite.expired.body': "Cette invitation n'est plus valide. Veuillez demander une nouvelle invitation à votre administrateur.",
      'invite.backLogin': 'Retour à la connexion',
      'invite.fullName': 'Nom complet',
      'invite.password': 'Mot de passe',
      'invite.confirmPassword': 'Confirmer le mot de passe',
      'invite.join': "Rejoindre l'organisation",
      'invite.member': 'Membre',
      'invite.defaultOrg': 'Votre organisation',
      'invite.error.passwordMismatch': 'Les mots de passe ne correspondent pas.',
      'invite.error.create': 'Erreur lors de la création du compte',
      'invite.error.server': 'Erreur de connexion au serveur',
      'invite.loading.create': 'Création du compte...',
    },
    ar: {
      'lang.label': 'اللغة',
      'lang.fr': 'Français',
      'lang.ar': 'العربية',
      'lang.en': 'English',
      'lang.current': 'اللغة الحالية: {language}',
      'common.loading': 'جار التحميل...',
      'common.online': 'متصل',
      'common.connected': 'متصل',
      'common.offline': 'غير متصل',
      'common.error': 'خطأ',
      'common.close': 'إغلاق',
      'common.cancel': 'إلغاء',
      'common.save': 'حفظ',
      'common.ignore': 'تجاهل',
      'common.search': 'بحث',
      'common.upload': 'رفع',
      'common.create': 'إنشاء',
      'common.delete': 'حذف',
      'common.details': 'تفاصيل',
      'common.back': 'رجوع',
      'common.previous': 'السابق',
      'common.next': 'التالي',
      'common.status': 'الحالة',
      'common.actions': 'إجراءات',
      'common.language': 'اللغة',
      'common.name': 'الاسم',
      'common.email': 'البريد الإلكتروني',
      'common.role': 'الدور',
      'common.type': 'النوع',
      'common.title': 'العنوان',
      'common.description': 'الوصف',
      'common.profile': 'الملف',
      'common.score': 'النتيجة',
      'common.frequency': 'التكرار',
      'common.evidence': 'الأدلة',
      'common.effectiveness': 'الفعالية',
      'common.risk': 'الخطر',
      'common.justification': 'التبرير',
      'common.owner': 'المالك',
      'common.due': 'الموعد',
      'common.priority': 'الأولوية',
      'common.assigned': 'مسند إلى',
      'common.updated': 'آخر تحديث',
      'common.createdAt': 'تاريخ الإنشاء',
      'common.expires': 'ينتهي',
      'common.subscription': '\u0627\u0644\u0627\u0634\u062a\u0631\u0627\u0643',
      'common.subscriptionEnd': '\u0646\u0647\u0627\u064a\u0629 \u0627\u0644\u0627\u0634\u062a\u0631\u0627\u0643',
      'common.sector': 'القطاع',
      'common.size': 'الحجم',
      'common.employees': 'الموظفون',
      'common.members': 'الأعضاء',
      'common.file': 'الملف',
      'common.analyzedType': 'النوع المحلل',
      'common.auto': 'تلقائي',
      'common.all': 'الكل',
      'common.allLanguages': 'كل اللغات',
      'common.french': 'الفرنسية',
      'common.arabic': 'العربية',
      'common.english': 'الإنجليزية',
      'common.page': 'صفحة',
      'common.total': 'المجموع',
      'common.none': 'لا يوجد',
      'common.notAvailable': 'غير متاح',
      'common.yes': 'نعم',
      'common.no': 'لا',
      'common.continue': 'متابعة',
      'common.select': 'اختر',
      'common.add': 'إضافة',
      'common.send': 'إرسال',
      'common.deactivate': 'تعطيل',
      'common.revoke': 'إلغاء',
      'common.noUsers': 'لا يوجد مستخدمون.',
      'common.noOrganizations': 'لا توجد مؤسسات.',
      'role.super_admin': 'مدير عام',
      'role.owner': 'المسيّر',
      'role.admin': 'مدير',
      'role.member': 'عضو',
      'role.viewer': 'قارئ',
      'status.active': 'نشط',
      'status.inactive': 'غير نشط',
      'status.pending': 'قيد الانتظار',
      'status.pending_approval': 'في انتظار الموافقة',
      'status.ready': 'جاهز',
      'status.processing': 'قيد المعالجة',
      'status.completed': 'مكتمل',
      'status.failed': 'فشل',
      'status.error': 'خطأ',
      'status.open': 'مفتوح',
      'status.in_progress': 'قيد التنفيذ',
      'status.under_review': 'قيد المراجعة',
      'status.resolved': 'محلول',
      'status.closed': 'مغلق',
      'status.cancelled': 'ملغى',
      'status.approved': 'مقبول',
      'status.rejected': 'مرفوض',
      'status.expired': 'منتهي',
      'status.revoked': 'ملغى',
      'status.draft': 'مسودة',
      'status.published': 'منشور',
      'status.not_analyzed': 'غير محلل',
      'status.applied': 'مطبق',
      'status.partial': 'جزئي',
      'status.covered': 'مغطى',
      'status.not_covered': 'غير مغطى',
      'subscription.monthly': '\u0634\u0647\u0631\u064a',
      'subscription.annual': '\u0633\u0646\u0648\u064a',
      'priority.critical': 'حرجة',
      'priority.high': 'عالية',
      'priority.medium': 'متوسطة',
      'priority.low': 'منخفضة',
      'severity.observation': 'ملاحظة',
      'severity.minor': 'بسيط',
      'severity.major': 'كبير',
      'docRole.evidence': 'دليل',
      'docRole.incoming_request': 'طلب وارد',
      'docRole.policy': 'سياسة',
      'docRole.contract': 'عقد',
      'docRole.authority_notice': 'إشعار سلطة',
      'docRole.other': 'أخرى',

      'index.title': 'دليل - Daleel | الخبير القانوني التونسي',
      'index.meta.description': 'مساعد قانوني ذكي متخصص في القانون التونسي. اطرح أسئلتك بالعربية أو الفرنسية أو الإنجليزية.',
      'index.brand.subtitle': 'خبير قانوني تونسي',
      'index.newChat': 'محادثة جديدة',
      'index.admin': 'الإدارة',
      'index.case': 'ملف',
      'index.nav.chat': 'الدردشة',
      'index.welcome.title': 'مرحباً بك في دليل',
      'index.welcome.body': 'مرحباً، أنا <strong>Daleel</strong> (دليل)، مستشارك القانوني المتخصص في القانون التونسي. أساعدك على فهم <strong>مجلة الشغل</strong> و<strong>مجلة الشركات التجارية</strong> و<strong>القانون عدد 63 لسنة 2004</strong> المتعلق بحماية المعطيات الشخصية. صف وضعيتك <strong>بالعربية</strong> أو <strong>بالفرنسية</strong> أو <strong>بالإنجليزية</strong>.',
      'index.suggestion.1': 'ما هي شروط تأسيس شركة في تونس؟',
      'index.suggestion.2': 'ما هي التزامات مدير الشركة ذات المسؤولية المحدودة؟',
      'index.suggestion.3': 'ما هي حقوق العامل عند الطرد التعسفي؟',
      'index.suggestion.4': 'كيف أحمي المعطيات الشخصية لحرفائي؟',
      'index.history.offline': 'الخادم غير متاح',
      'index.history.loginRequired': 'تسجيل الدخول مطلوب',
      'index.input.placeholder': 'اطرح سؤالك القانوني...',
      'index.input.hint': 'اضغط Enter للإرسال',
      'index.send': 'إرسال',
      'index.sources.used': '{count} مصدر مستخدم',
      'index.feedback.title': 'اقتراح تصحيح',
      'index.feedback.placeholder': 'ضع هنا الإجابة المصححة...',
      'index.feedback.tooShort': 'التصحيح قصير جداً.',
      'index.feedback.saving': 'جار الحفظ...',
      'index.feedback.saved': 'تم حفظ التصحيح.',
      'index.feedback.failed': 'فشل الحفظ.',
      'index.feedback.network': 'خطأ في الشبكة.',
      'index.error.generic': 'حدث خطأ. يرجى المحاولة مرة أخرى.',
      'index.error.api': 'تعذر الاتصال بواجهة البرمجة. تأكد من أن الخادم يعمل ويمكن الوصول إليه.',
      'index.error.detail': 'التفاصيل: {message}',
      'index.case.prompt': 'عنوان ملف الامتثال:',
      'index.case.created': 'تم إنشاء الملف: **{title}**\n\nيمكنك الاطلاع عليه في لوحة الإدارة: [فتح الملف](/admin)',
      'index.case.createError': 'حدث خطأ أثناء إنشاء الملف.',
      'index.case.network': 'خطأ في الاتصال.',

      'admin.title': 'إدارة دليل - منصة الامتثال',
      'admin.nav.principal': 'الرئيسي',
      'admin.nav.dashboard': 'لوحة التحكم',
      'admin.nav.documents': 'الوثائق',
      'admin.nav.compliance': 'الامتثال',
      'admin.nav.amendments': 'التعديلات',
      'admin.nav.history': 'السجل',
      'admin.nav.cases': 'الملفات',
      'admin.nav.companyProfile': 'ملف المؤسسة',
      'admin.nav.users': 'المستخدمون',
      'admin.nav.organizations': 'المؤسسات',
      'admin.nav.userManagement': 'إدارة المستخدمين',
      'admin.nav.actions': 'الإجراءات',
      'admin.nav.notifications': 'الإشعارات',
      'admin.nav.administration': 'الإدارة',
      'admin.footer.chat': 'الدردشة',
      'admin.footer.logout': 'تسجيل الخروج',
      'admin.dashboard.recentActivity': 'النشاط الأخير',
      'admin.dashboard.noEvents': 'لا توجد أحداث',
      'admin.dashboard.serverOffline': 'الخادم غير متاح',
      'admin.dashboard.serverOfflineHint': 'قم بتشغيل الخادم لعرض بيانات لوحة القيادة.',
      'admin.dashboard.vectorEngine': 'محرك المتجهات',
      'admin.dashboard.actionCriticality': 'أهمية الإجراءات',
      'admin.dashboard.questionsPerDay': 'الأسئلة / اليوم (30 يوماً)',
      'admin.dashboard.avgSatisfaction': 'متوسط الرضا (30 يوماً)',
      'admin.dashboard.coverageByProfile': 'تغطية الامتثال حسب الملف',
      'admin.dashboard.notifications': 'الإشعارات',
      'admin.dashboard.noEvent': 'لا توجد أحداث',
      'admin.dashboard.noNotification': 'لا توجد إشعارات',
      'admin.dashboard.laws': 'القوانين',
      'admin.dashboard.requirements': 'المتطلبات',
      'admin.dashboard.profiles': 'الملفات',
      'admin.dashboard.pendingSuffix': 'قيد الانتظار',
      'admin.dashboard.withCriticality': 'مع أهمية',
      'admin.documents.title': 'الوثائق',
      'admin.documents.inDatabase': '{count} وثيقة في القاعدة',
      'admin.documents.file': 'الملف',
      'admin.documents.type': 'النوع',
      'admin.documents.pages': 'الصفحات',
      'admin.documents.chunks': 'المقاطع',
      'admin.documents.classify': 'تصنيف',
      'admin.documents.uploadHint': 'انقر أو اسحب ملفاً (PDF أو DOCX أو TXT)',
      'admin.laws.title': 'القوانين والفصول',
      'admin.laws.create': 'إنشاء قانون',
      'admin.laws.code': 'الرمز',
      'admin.laws.name': 'الاسم',
      'admin.laws.description': 'الوصف',
      'admin.laws.bilingual': 'ثنائي اللغة',
      'admin.laws.createButton': 'إنشاء القانون',
      'admin.laws.articles': 'الفصول',
      'admin.laws.segment': 'تقسيم',
      'admin.laws.criticality': 'الأهمية',
      'admin.search.qa': 'أسئلة/أجوبة قانونية',
      'admin.search.userQuestion': 'سؤال المستخدم',
      'admin.search.askPlaceholder': 'مثال: ما الحل العملي للامتثال لواجبات مسك السجلات؟',
      'admin.search.autoMode': 'وضع تلقائي (اختيار ذكي)',
      'admin.search.classicMode': 'وضع كلاسيكي (/ask)',
      'admin.search.agenticMode': 'وضع agentic (/ask-agentic)',
      'admin.search.ask': 'طرح السؤال',
      'admin.search.compare': 'مقارنة الكلاسيكي مع agentic',
      'admin.search.tip': 'نصيحة: Ctrl+Enter للتشغيل بسرعة.',
      'admin.search.semantic': 'بحث دلالي',
      'admin.search.placeholder': 'ابحث في الوثائق القانونية... (FR أو AR أو EN)',
      'admin.users.members': 'الأعضاء',
      'admin.users.invite': 'دعوة',
      'admin.users.pendingInvites': 'الدعوات الجارية',
      'admin.users.email': 'البريد الإلكتروني',
      'admin.users.role': 'الدور',
      'admin.users.lastLogin': 'آخر تسجيل دخول',
      'admin.users.active': 'نشط',
      'admin.users.inviteMember': 'دعوة عضو',
      'admin.users.noOrganization': 'لا توجد مؤسسة مرتبطة بهذا الحساب.',
      'admin.users.inviteSent': 'تم إرسال الدعوة',
      'admin.users.roleUpdated': 'تم تحديث الدور',
      'admin.users.statusUpdated': 'تم تحديث الحالة',
      'admin.users.userDisabled': 'تم تعطيل المستخدم',
      'admin.users.invitationRevoked': 'تم إلغاء الدعوة',
      'admin.users.confirmDeactivate': 'هل تريد تعطيل هذا المستخدم؟',
      'admin.users.confirmRevoke': 'هل تريد إلغاء هذه الدعوة؟',
      'admin.organizations.title': 'المؤسسات',
      'admin.administration.title': 'الإدارة',
      'admin.adminTabs.laws': 'القوانين والفصول',
      'admin.adminTabs.cases': 'الملفات',
      'admin.adminTabs.posture': 'الوضعية',
      'admin.adminTabs.assessments': 'التقييمات',
      'admin.adminTabs.controls': 'الضوابط',
      'admin.adminTabs.exceptions': 'الاستثناءات',
      'admin.adminTabs.audit': 'سجل التدقيق',
      'admin.adminTabs.search': 'البحث',
      'admin.adminTabs.vectors': 'المتجهات',
      'admin.cases.title': 'ملفات الامتثال',
      'admin.cases.new': 'ملف جديد',
      'admin.cases.allPriorities': 'كل الأولويات',
      'admin.cases.confirmDelete': 'هل تريد حذف هذا الملف؟',
      'admin.cases.deleted': 'تم حذف الملف',
      'admin.amendments.title': 'التعديلات - تحديث الوثائق',
      'admin.amendments.subtitle': 'ارفع نسخة جديدة من وثيقة. يكتشف النظام القانون المستهدف تلقائياً، ويقارن الفصول، وينبّه ملفات المؤسسات.',
      'admin.amendments.uploadTitle': 'رفع وثيقة معدلة',
      'admin.amendments.uploadDescription': 'يكتشف النظام القانون المستهدف تلقائياً من محتوى الوثيقة، ويقارن الفصول، وينبّه ملفات المؤسسات بالتغييرات.',
      'admin.amendments.documentLabel': 'وثيقة (PDF أو DOCX)',
      'admin.amendments.dropPrefix': 'اسحب ملفاً هنا أو',
      'admin.amendments.browse': 'تصفح',
      'admin.amendments.compareUpdate': 'قارن وحدّث',
      'admin.history.title': 'سجل المحادثات',
      'admin.history.allMembers': 'كل الأعضاء',
      'admin.history.user': 'المستخدم',
      'admin.history.question': 'السؤال',
      'admin.history.answerPreview': 'الإجابة (معاينة)',
      'admin.history.sources': 'المصادر',
      'admin.history.date': 'التاريخ',
      'admin.history.none': 'لا توجد محادثات مسجلة',
      'admin.company.info': 'معلومات المؤسسة',
      'admin.company.statistics': 'الإحصائيات',

      'auth.title': 'دليل - تسجيل الدخول',
      'auth.subtitle': 'منصة الامتثال القانوني التونسية',
      'auth.loginTab': 'تسجيل الدخول',
      'auth.registerTab': 'إنشاء حساب',
      'auth.email': 'البريد الإلكتروني',
      'auth.workEmail': 'البريد المهني',
      'auth.password': 'كلمة المرور',
      'auth.login': 'دخول',
      'auth.fullName': 'الاسم الكامل',
      'auth.fullName.placeholder': 'اسمك الكامل',
      'auth.password.placeholder': 'كلمة المرور',
      'auth.password.minPlaceholder': '8 أحرف على الأقل',
      'auth.confirmPassword': 'تأكيد كلمة المرور',
      'auth.confirmPassword.placeholder': 'أعد إدخال كلمة المرور',
      'auth.personalInfo': 'المعلومات الشخصية',
      'auth.personalInfo.subtitle': 'أنشئ حساب المدير',
      'auth.sector.title': 'قطاع النشاط',
      'auth.sector.subtitle': 'اختر قطاع نشاط مؤسستك',
      'auth.company.title': 'ملف المؤسسة',
      'auth.company.subtitle': 'أكمل معلومات منظمتك',
      'auth.company.name': 'اسم المؤسسة',
      'auth.company.placeholder': 'مثال: TechnoTunisie SARL',
      'auth.subscription.type': '\u0646\u0648\u0639 \u0627\u0644\u0627\u0634\u062a\u0631\u0627\u0643',
      'auth.size': 'الحجم',
      'auth.employees': 'عدد الموظفين',
      'auth.employees.placeholder': 'مثال: 50',
      'auth.jurisdiction': 'الاختصاص',
      'auth.tunisia': 'تونس',
      'auth.createAccount': 'إنشاء حسابي',
      'auth.footer': 'Daleel v1.0 - امتثال قانوني ذكي',
      'auth.error.required': 'يرجى تعمير كل الحقول. يجب أن تتكوّن كلمة المرور من 8 أحرف على الأقل.',
      'auth.error.sector': 'يرجى اختيار قطاع النشاط.',
      'auth.error.organization': 'يرجى إدخال اسم مؤسستك.',
      'auth.error.passwordMismatch': 'كلمتا المرور غير متطابقتين.',
      'auth.error.login': 'البريد الإلكتروني أو كلمة المرور غير صحيحة',
      'auth.error.server': 'خطأ في الاتصال بالخادم',
      'auth.error.register': 'حدث خطأ أثناء التسجيل',
      'auth.registrationPending': 'تم إرسال طلب التسجيل إلى المدير العام. يمكنك تسجيل الدخول بعد الموافقة.',
      'auth.loading.login': 'جار تسجيل الدخول...',
      'auth.loading.register': 'جار الإنشاء...',
      'auth.sector.finance': 'المالية',
      'auth.sector.banque': 'البنوك',
      'auth.sector.assurance': 'التأمين',
      'auth.sector.industrie': 'الصناعة',
      'auth.sector.technologie': 'التكنولوجيا',
      'auth.sector.telecom': 'الاتصالات',
      'auth.sector.sante': 'الصحة',
      'auth.sector.pharma': 'الأدوية',
      'auth.sector.transport': 'النقل',
      'auth.sector.btp': 'البناء',
      'auth.sector.commerce': 'التجارة',
      'auth.sector.energie': 'الطاقة',
      'auth.sector.education': 'التعليم',
      'auth.sector.agriculture': 'الفلاحة',
      'auth.sector.tourisme': 'السياحة',
      'auth.sector.services': 'الخدمات',
      'auth.sector.immobilier': 'العقارات',
      'auth.sector.autre': 'أخرى',
      'auth.size.micro': 'صغرى (1-9)',
      'auth.size.small': 'صغيرة (10-49)',
      'auth.size.medium': 'متوسطة (50-249)',
      'auth.size.large': 'كبيرة (250+)',

      'invite.title': 'دليل - دعوة',
      'invite.subtitle': 'تمت دعوتك للانضمام إلى منظمة',
      'invite.loading': 'جار التحقق من الدعوة...',
      'invite.expired.title': 'انتهت صلاحية الدعوة',
      'invite.expired.body': 'هذه الدعوة لم تعد صالحة. يرجى طلب دعوة جديدة من المدير.',
      'invite.backLogin': 'العودة إلى تسجيل الدخول',
      'invite.fullName': 'الاسم الكامل',
      'invite.password': 'كلمة المرور',
      'invite.confirmPassword': 'تأكيد كلمة المرور',
      'invite.join': 'الانضمام إلى المنظمة',
      'invite.member': 'عضو',
      'invite.defaultOrg': 'منظمتك',
      'invite.error.passwordMismatch': 'كلمتا المرور غير متطابقتين.',
      'invite.error.create': 'حدث خطأ أثناء إنشاء الحساب',
      'invite.error.server': 'خطأ في الاتصال بالخادم',
      'invite.loading.create': 'جار إنشاء الحساب...',
    },
    en: {
      'lang.label': 'Language',
      'lang.fr': 'Français',
      'lang.ar': 'العربية',
      'lang.en': 'English',
      'lang.current': 'Current language: {language}',
      'common.loading': 'Loading...',
      'common.online': 'Online',
      'common.connected': 'Connected',
      'common.offline': 'Offline',
      'common.error': 'Error',
      'common.close': 'Close',
      'common.cancel': 'Cancel',
      'common.save': 'Save',
      'common.ignore': 'Ignore',
      'common.search': 'Search',
      'common.upload': 'Upload',
      'common.create': 'Create',
      'common.delete': 'Delete',
      'common.details': 'Details',
      'common.back': 'Back',
      'common.previous': 'Prev.',
      'common.next': 'Next',
      'common.status': 'Status',
      'common.actions': 'Actions',
      'common.language': 'Language',
      'common.name': 'Name',
      'common.email': 'Email',
      'common.role': 'Role',
      'common.type': 'Type',
      'common.title': 'Title',
      'common.description': 'Description',
      'common.profile': 'Profile',
      'common.score': 'Score',
      'common.frequency': 'Frequency',
      'common.evidence': 'Evidence',
      'common.effectiveness': 'Eff.',
      'common.risk': 'Risk',
      'common.justification': 'Justification',
      'common.owner': 'Owner',
      'common.due': 'Due',
      'common.priority': 'Priority',
      'common.assigned': 'Assigned',
      'common.updated': 'Updated',
      'common.createdAt': 'Created on',
      'common.expires': 'Expires',
      'common.subscription': 'Subscription',
      'common.subscriptionEnd': 'Subscription end',
      'common.sector': 'Sector',
      'common.size': 'Size',
      'common.employees': 'Employees',
      'common.members': 'Members',
      'common.file': 'File',
      'common.analyzedType': 'Analyzed type',
      'common.auto': 'Auto',
      'common.all': 'All',
      'common.allLanguages': 'All languages',
      'common.french': 'French',
      'common.arabic': 'Arabic',
      'common.english': 'English',
      'common.page': 'Page',
      'common.total': 'total',
      'common.none': 'None',
      'common.notAvailable': 'Not available',
      'common.yes': 'Yes',
      'common.no': 'No',
      'common.continue': 'Continue',
      'common.select': 'Select',
      'common.add': 'Add',
      'common.send': 'Send',
      'common.deactivate': 'Deactivate',
      'common.revoke': 'Revoke',
      'common.noUsers': 'No users.',
      'common.noOrganizations': 'No organizations.',
      'role.super_admin': 'Super Admin',
      'role.owner': 'Manager',
      'role.admin': 'Admin',
      'role.member': 'Member',
      'role.viewer': 'Viewer',
      'status.active': 'Active',
      'status.inactive': 'Inactive',
      'status.pending': 'Pending',
      'status.pending_approval': 'Pending approval',
      'status.ready': 'Ready',
      'status.processing': 'Processing',
      'status.completed': 'Completed',
      'status.failed': 'Failed',
      'status.error': 'Error',
      'status.open': 'Open',
      'status.in_progress': 'In progress',
      'status.under_review': 'Under review',
      'status.resolved': 'Resolved',
      'status.closed': 'Closed',
      'status.cancelled': 'Cancelled',
      'status.approved': 'Approved',
      'status.rejected': 'Rejected',
      'status.expired': 'Expired',
      'status.revoked': 'Revoked',
      'status.draft': 'Draft',
      'status.published': 'Published',
      'status.not_analyzed': 'Not analyzed',
      'status.applied': 'Applied',
      'status.partial': 'Partial',
      'status.covered': 'Covered',
      'status.not_covered': 'Not covered',
      'subscription.monthly': 'Monthly',
      'subscription.annual': 'Annual',
      'priority.critical': 'Critical',
      'priority.high': 'High',
      'priority.medium': 'Medium',
      'priority.low': 'Low',
      'severity.observation': 'Observation',
      'severity.minor': 'Minor',
      'severity.major': 'Major',
      'docRole.evidence': 'Evidence',
      'docRole.incoming_request': 'Incoming request',
      'docRole.policy': 'Policy',
      'docRole.contract': 'Contract',
      'docRole.authority_notice': 'Authority notice',
      'docRole.other': 'Other',

      'index.title': 'Daleel - دليل | Tunisian Legal Expert',
      'index.meta.description': 'An intelligent legal assistant specialized in Tunisian law. Ask questions in Arabic, French, or English.',
      'index.brand.subtitle': 'Tunisian Legal Expert',
      'index.newChat': 'New chat',
      'index.admin': 'Admin',
      'index.case': 'Case',
      'index.nav.chat': 'Chat',
      'index.welcome.title': 'Welcome to Daleel',
      'index.welcome.body': 'Hello, I am <strong>Daleel</strong> (دليل), your legal advisor specialized in Tunisian law. I help you understand the <strong>Labor Code</strong>, the <strong>Commercial Companies Code</strong>, and <strong>Law 63-2004</strong> on personal data protection. Describe your situation in <strong>Arabic</strong>, <strong>French</strong>, or <strong>English</strong>.',
      'index.suggestion.1': 'What are the requirements to create a company in Tunisia?',
      'index.suggestion.2': 'What are the obligations of a SARL manager?',
      'index.suggestion.3': "What are workers' rights in case of unfair dismissal?",
      'index.suggestion.4': "How can I protect my customers' personal data?",
      'index.history.offline': 'Server unavailable',
      'index.history.loginRequired': 'Login required',
      'index.input.placeholder': 'Ask your legal question...',
      'index.input.hint': 'Press Enter to send',
      'index.send': 'Send',
      'index.sources.used': '{count} source{plural} used',
      'index.feedback.title': 'Suggest a correction',
      'index.feedback.placeholder': 'Paste the corrected answer here...',
      'index.feedback.tooShort': 'The correction is too short.',
      'index.feedback.saving': 'Saving...',
      'index.feedback.saved': 'Correction saved.',
      'index.feedback.failed': 'Save failed.',
      'index.feedback.network': 'Network error.',
      'index.error.generic': 'Something went wrong. Please try again.',
      'index.error.api': 'Unable to reach the API. Check that the server is running and accessible.',
      'index.error.detail': 'Detail: {message}',
      'index.case.prompt': 'Compliance case title:',
      'index.case.created': 'Case created: **{title}**\n\nYou can review it in admin: [Open case](/admin)',
      'index.case.createError': 'Error while creating the case.',
      'index.case.network': 'Connection error.',

      'admin.title': 'Daleel Admin - Compliance Platform',
      'admin.nav.principal': 'Principal',
      'admin.nav.dashboard': 'Dashboard',
      'admin.nav.documents': 'Documents',
      'admin.nav.compliance': 'Compliance',
      'admin.nav.amendments': 'Amendments',
      'admin.nav.history': 'History',
      'admin.nav.cases': 'Cases',
      'admin.nav.companyProfile': 'Company profile',
      'admin.nav.users': 'Users',
      'admin.nav.organizations': 'Organizations',
      'admin.nav.userManagement': 'User management',
      'admin.nav.actions': 'Actions',
      'admin.nav.notifications': 'Notifications',
      'admin.nav.administration': 'Administration',
      'admin.footer.chat': 'Chat',
      'admin.footer.logout': 'Log out',
      'admin.dashboard.recentActivity': 'Recent activity',
      'admin.dashboard.noEvents': 'No events',
      'admin.dashboard.serverOffline': 'Server unavailable',
      'admin.dashboard.serverOfflineHint': 'Start the backend to see dashboard data.',
      'admin.dashboard.vectorEngine': 'Vector engine',
      'admin.dashboard.actionCriticality': 'Action criticality',
      'admin.dashboard.questionsPerDay': 'Questions / day (30d)',
      'admin.dashboard.avgSatisfaction': 'Average satisfaction (30d)',
      'admin.dashboard.coverageByProfile': 'Compliance coverage by profile',
      'admin.dashboard.notifications': 'Notifications',
      'admin.dashboard.noEvent': 'No event',
      'admin.dashboard.noNotification': 'No notification',
      'admin.dashboard.laws': 'Laws',
      'admin.dashboard.requirements': 'Requirements',
      'admin.dashboard.profiles': 'Profiles',
      'admin.dashboard.pendingSuffix': 'pending',
      'admin.dashboard.withCriticality': 'with criticality',
      'admin.documents.title': 'Documents',
      'admin.documents.inDatabase': '{count} document(s) in the database',
      'admin.documents.file': 'File',
      'admin.documents.type': 'Type',
      'admin.documents.pages': 'Pages',
      'admin.documents.chunks': 'Chunks',
      'admin.documents.classify': 'Classify',
      'admin.documents.uploadHint': 'Click or drop a file (PDF, DOCX, TXT)',
      'admin.laws.title': 'Laws & Articles',
      'admin.laws.create': 'Create a law',
      'admin.laws.code': 'Code',
      'admin.laws.name': 'Name',
      'admin.laws.description': 'Description',
      'admin.laws.bilingual': 'Bilingual',
      'admin.laws.createButton': 'Create law',
      'admin.laws.articles': 'Articles',
      'admin.laws.segment': 'Segment',
      'admin.laws.criticality': 'Criticality',
      'admin.search.qa': 'Legal Q&A',
      'admin.search.userQuestion': 'User question',
      'admin.search.askPlaceholder': 'Example: What practical solution helps comply with register keeping obligations?',
      'admin.search.autoMode': 'Auto mode (smart choice)',
      'admin.search.classicMode': 'Classic mode (/ask)',
      'admin.search.agenticMode': 'Agentic mode (/ask-agentic)',
      'admin.search.ask': 'Ask question',
      'admin.search.compare': 'Compare classic vs agentic',
      'admin.search.tip': 'Tip: Ctrl+Enter to run quickly.',
      'admin.search.semantic': 'Semantic search',
      'admin.search.placeholder': 'Search legal documents... (FR, AR, or EN)',
      'admin.users.members': 'Members',
      'admin.users.invite': 'Invite',
      'admin.users.pendingInvites': 'Pending invitations',
      'admin.users.email': 'Email',
      'admin.users.role': 'Role',
      'admin.users.lastLogin': 'Last login',
      'admin.users.active': 'Active',
      'admin.users.inviteMember': 'Invite member',
      'admin.users.noOrganization': 'No organization is associated with this account.',
      'admin.users.inviteSent': 'Invitation sent',
      'admin.users.roleUpdated': 'Role updated',
      'admin.users.statusUpdated': 'Status updated',
      'admin.users.userDisabled': 'User deactivated',
      'admin.users.invitationRevoked': 'Invitation revoked',
      'admin.users.confirmDeactivate': 'Deactivate this user?',
      'admin.users.confirmRevoke': 'Revoke this invitation?',
      'admin.organizations.title': 'Organizations',
      'admin.administration.title': 'Administration',
      'admin.adminTabs.laws': 'Laws & Articles',
      'admin.adminTabs.cases': 'Cases',
      'admin.adminTabs.posture': 'Posture',
      'admin.adminTabs.assessments': 'Assessments',
      'admin.adminTabs.controls': 'Controls',
      'admin.adminTabs.exceptions': 'Exceptions',
      'admin.adminTabs.audit': 'Audit log',
      'admin.adminTabs.search': 'Search',
      'admin.adminTabs.vectors': 'Vectors',
      'admin.cases.title': 'Compliance cases',
      'admin.cases.new': 'New case',
      'admin.cases.allPriorities': 'All priorities',
      'admin.cases.confirmDelete': 'Delete this case?',
      'admin.cases.deleted': 'Case deleted',
      'admin.amendments.title': 'Amendments - Document update',
      'admin.amendments.subtitle': 'Upload a new version of a document. The system automatically detects the target law, compares articles, and notifies company profiles.',
      'admin.amendments.uploadTitle': 'Upload an amended document',
      'admin.amendments.uploadDescription': 'The system automatically detects the target law from the document content, compares articles, and notifies company profiles about changes.',
      'admin.amendments.documentLabel': 'Document (PDF or DOCX)',
      'admin.amendments.dropPrefix': 'Drop a file here or',
      'admin.amendments.browse': 'browse',
      'admin.amendments.compareUpdate': 'Compare & update',
      'admin.history.title': 'Conversation history',
      'admin.history.allMembers': 'All members',
      'admin.history.user': 'User',
      'admin.history.question': 'Question',
      'admin.history.answerPreview': 'Answer (preview)',
      'admin.history.sources': 'Sources',
      'admin.history.date': 'Date',
      'admin.history.none': 'No saved conversation',
      'admin.company.info': 'Company information',
      'admin.company.statistics': 'Statistics',

      'auth.title': 'Daleel - Sign in',
      'auth.subtitle': 'Tunisian legal compliance platform',
      'auth.loginTab': 'Sign in',
      'auth.registerTab': 'Register',
      'auth.email': 'Email',
      'auth.workEmail': 'Work email',
      'auth.password': 'Password',
      'auth.login': 'Sign in',
      'auth.fullName': 'Full name',
      'auth.fullName.placeholder': 'Your full name',
      'auth.password.placeholder': 'Your password',
      'auth.password.minPlaceholder': 'Minimum 8 characters',
      'auth.confirmPassword': 'Confirm password',
      'auth.confirmPassword.placeholder': 'Confirm your password',
      'auth.personalInfo': 'Personal information',
      'auth.personalInfo.subtitle': 'Create your administrator account',
      'auth.sector.title': 'Business sector',
      'auth.sector.subtitle': 'Select your company sector',
      'auth.company.title': 'Company profile',
      'auth.company.subtitle': 'Complete your organization information',
      'auth.company.name': 'Company name',
      'auth.company.placeholder': 'Ex: TechnoTunisie SARL',
      'auth.subscription.type': 'Subscription type',
      'auth.size': 'Size',
      'auth.employees': 'Number of employees',
      'auth.employees.placeholder': 'Ex: 50',
      'auth.jurisdiction': 'Jurisdiction',
      'auth.tunisia': 'Tunisia',
      'auth.createAccount': 'Create my account',
      'auth.footer': 'Daleel v1.0 - Intelligent legal compliance',
      'auth.error.required': 'Please fill in all fields. The password must contain at least 8 characters.',
      'auth.error.sector': 'Please select a business sector.',
      'auth.error.organization': 'Please enter your company name.',
      'auth.error.passwordMismatch': 'Passwords do not match.',
      'auth.error.login': 'Incorrect email or password',
      'auth.error.server': 'Server connection error',
      'auth.error.register': 'Registration error',
      'auth.registrationPending': 'Your registration was sent to the super admin. You can sign in after approval.',
      'auth.loading.login': 'Signing in...',
      'auth.loading.register': 'Creating...',
      'auth.sector.finance': 'Finance',
      'auth.sector.banque': 'Banking',
      'auth.sector.assurance': 'Insurance',
      'auth.sector.industrie': 'Industry',
      'auth.sector.technologie': 'Technology',
      'auth.sector.telecom': 'Telecom',
      'auth.sector.sante': 'Health',
      'auth.sector.pharma': 'Pharma',
      'auth.sector.transport': 'Transport',
      'auth.sector.btp': 'Construction',
      'auth.sector.commerce': 'Commerce',
      'auth.sector.energie': 'Energy',
      'auth.sector.education': 'Education',
      'auth.sector.agriculture': 'Agriculture',
      'auth.sector.tourisme': 'Tourism',
      'auth.sector.services': 'Services',
      'auth.sector.immobilier': 'Real estate',
      'auth.sector.autre': 'Other',
      'auth.size.micro': 'Micro (1-9)',
      'auth.size.small': 'Small (10-49)',
      'auth.size.medium': 'Medium (50-249)',
      'auth.size.large': 'Large (250+)',

      'invite.title': 'Daleel - Invitation',
      'invite.subtitle': 'You have been invited to join an organization',
      'invite.loading': 'Checking invitation...',
      'invite.expired.title': 'Invitation expired',
      'invite.expired.body': 'This invitation is no longer valid. Please ask your administrator for a new invitation.',
      'invite.backLogin': 'Back to sign in',
      'invite.fullName': 'Full name',
      'invite.password': 'Password',
      'invite.confirmPassword': 'Confirm password',
      'invite.join': 'Join organization',
      'invite.member': 'Member',
      'invite.defaultOrg': 'Your organization',
      'invite.error.passwordMismatch': 'Passwords do not match.',
      'invite.error.create': 'Error while creating the account',
      'invite.error.server': 'Server connection error',
      'invite.loading.create': 'Creating account...',
    },
  };

  const phraseKeys = [
    'common.loading',
    'common.online',
    'common.connected',
    'common.offline',
    'common.error',
    'common.close',
    'common.cancel',
    'common.save',
    'common.ignore',
    'common.search',
    'common.upload',
    'common.create',
    'common.delete',
    'common.details',
    'common.back',
    'common.previous',
    'common.next',
    'common.status',
    'common.actions',
    'common.language',
    'common.auto',
    'common.allLanguages',
    'common.french',
    'common.arabic',
    'common.english',
    'common.page',
    'common.notAvailable',
    'admin.nav.principal',
    'admin.nav.dashboard',
    'admin.nav.documents',
    'admin.nav.compliance',
    'admin.nav.amendments',
    'admin.nav.history',
    'admin.nav.companyProfile',
    'admin.nav.users',
    'admin.nav.organizations',
    'admin.nav.userManagement',
    'admin.nav.administration',
    'admin.footer.chat',
    'admin.footer.logout',
    'admin.dashboard.recentActivity',
    'admin.dashboard.vectorEngine',
    'admin.dashboard.actionCriticality',
    'admin.dashboard.questionsPerDay',
    'admin.dashboard.avgSatisfaction',
    'admin.dashboard.coverageByProfile',
    'admin.dashboard.notifications',
    'admin.dashboard.noEvent',
    'admin.dashboard.noNotification',
    'admin.documents.title',
    'admin.documents.file',
    'admin.documents.type',
    'admin.documents.pages',
    'admin.documents.chunks',
    'admin.documents.classify',
    'admin.documents.uploadHint',
    'admin.laws.title',
    'admin.laws.create',
    'admin.laws.code',
    'admin.laws.name',
    'admin.laws.description',
    'admin.laws.bilingual',
    'admin.laws.createButton',
    'admin.laws.articles',
    'admin.laws.segment',
    'admin.laws.criticality',
    'admin.search.qa',
    'admin.search.userQuestion',
    'admin.search.askPlaceholder',
    'admin.search.autoMode',
    'admin.search.classicMode',
    'admin.search.agenticMode',
    'admin.search.ask',
    'admin.search.compare',
    'admin.search.tip',
    'admin.search.semantic',
    'admin.search.placeholder',
    'admin.users.members',
    'admin.users.invite',
    'admin.users.pendingInvites',
    'admin.users.email',
    'admin.users.role',
    'admin.users.lastLogin',
    'admin.users.active',
    'admin.organizations.title',
    'admin.administration.title',
    'admin.adminTabs.laws',
    'admin.adminTabs.cases',
    'admin.adminTabs.posture',
    'admin.adminTabs.assessments',
    'admin.adminTabs.controls',
    'admin.adminTabs.exceptions',
    'admin.adminTabs.audit',
    'admin.adminTabs.search',
    'admin.adminTabs.vectors',
  ];

  const aliases = {
    'admin.nav.dashboard': ['Dashboard'],
    'admin.nav.compliance': ['Conformité'],
    'admin.nav.companyProfile': ['Profil Entreprise'],
    'admin.footer.logout': ['Déconnexion'],
    'admin.documents.classify': ['Classifier'],
    'admin.laws.create': ['Créer une Loi'],
    'admin.laws.createButton': ['Créer la Loi'],
    'admin.search.semantic': ['Recherche Sémantique'],
    'common.upload': ['Uploader'],
  };

  const phraseIndex = new Map();

  function normalizePhrase(value) {
    return String(value || '').replace(/\s+/g, ' ').trim().toLowerCase();
  }

  function rebuildPhraseIndex() {
    phraseIndex.clear();
    phraseKeys.forEach((key) => {
      SUPPORTED.forEach((lang) => {
        phraseIndex.set(normalizePhrase(dict[lang][key]), key);
      });
      (aliases[key] || []).forEach((value) => phraseIndex.set(normalizePhrase(value), key));
    });
  }

  function normalizeLang(value) {
    const base = String(value || '').toLowerCase().split('-')[0];
    return SUPPORTED.includes(base) ? base : null;
  }

  function detectBrowserLanguage() {
    const languages = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || navigator.userLanguage || 'fr'];
    for (const candidate of languages) {
      const normalized = normalizeLang(candidate);
      if (normalized) return normalized;
    }
    return 'fr';
  }

  function getLang() {
    return normalizeLang(localStorage.getItem(STORAGE_KEY)) || detectBrowserLanguage();
  }

  function format(template, params = {}) {
    return String(template).replace(/\{(\w+)\}/g, (_, key) => params[key] ?? '');
  }

  function t(key, params = {}) {
    const lang = getLang();
    const value = dict[lang]?.[key] ?? dict.fr[key] ?? key;
    return format(value, params);
  }

  function translatePhrase(value) {
    const key = phraseIndex.get(normalizePhrase(value));
    return key ? t(key) : null;
  }

  function applyDocumentLanguage() {
    const lang = getLang();
    document.documentElement.lang = lang;
    document.documentElement.dir = RTL.has(lang) ? 'rtl' : 'ltr';
    document.body?.setAttribute('dir', RTL.has(lang) ? 'rtl' : 'ltr');
  }

  function setElementText(el, value, html = false) {
    if (html) el.innerHTML = value;
    else el.textContent = value;
  }

  function matchingElements(root, selector) {
    const scoped = root.nodeType === Node.ELEMENT_NODE ? root : document;
    const items = [];
    if (scoped.matches?.(selector)) items.push(scoped);
    scoped.querySelectorAll?.(selector).forEach((el) => items.push(el));
    return items;
  }

  function translateAttributes(root) {
    matchingElements(root, '[data-i18n]').forEach((el) => setElementText(el, t(el.dataset.i18n)));
    matchingElements(root, '[data-i18n-html]').forEach((el) => setElementText(el, t(el.dataset.i18nHtml), true));
    matchingElements(root, '[data-i18n-placeholder]').forEach((el) => {
      el.setAttribute('placeholder', t(el.dataset.i18nPlaceholder));
    });
    matchingElements(root, '[data-i18n-title]').forEach((el) => {
      el.setAttribute('title', t(el.dataset.i18nTitle));
    });
    matchingElements(root, '[data-i18n-aria-label]').forEach((el) => {
      el.setAttribute('aria-label', t(el.dataset.i18nAriaLabel));
    });
  }

  function translateTextNodes(root) {
    const start = root.nodeType === Node.ELEMENT_NODE || root.nodeType === Node.DOCUMENT_NODE
      ? root
      : document.body;
    if (!start) return;

    const walker = document.createTreeWalker(
      start,
      NodeFilter.SHOW_TEXT,
      {
        acceptNode(node) {
          const parent = node.parentElement;
          if (!parent) return NodeFilter.FILTER_REJECT;
          if (['SCRIPT', 'STYLE', 'TEXTAREA', 'INPUT', 'CODE', 'PRE'].includes(parent.tagName)) {
            return NodeFilter.FILTER_REJECT;
          }
          if (!node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
          return NodeFilter.FILTER_ACCEPT;
        },
      }
    );

    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);

    nodes.forEach((node) => {
      const original = node.nodeValue;
      const leading = original.match(/^\s*/)?.[0] || '';
      const trailing = original.match(/\s*$/)?.[0] || '';
      const translated = translatePhrase(original.trim());
      if (translated && translated !== original.trim()) {
        node.nodeValue = `${leading}${translated}${trailing}`;
      }
    });
  }

  function translateMatchedAttributes(root) {
    matchingElements(root, '[placeholder]').forEach((el) => {
      const translated = translatePhrase(el.getAttribute('placeholder'));
      if (translated) el.setAttribute('placeholder', translated);
    });
    matchingElements(root, '[title]').forEach((el) => {
      const translated = translatePhrase(el.getAttribute('title'));
      if (translated) el.setAttribute('title', translated);
    });
  }

  let isApplying = false;

  function apply(root = document) {
    if (isApplying) return;
    isApplying = true;
    applyDocumentLanguage();
    translateAttributes(root);
    translateMatchedAttributes(root);
    translateTextNodes(root);
    isApplying = false;
    updateLanguageSwitchers();
  }

  function setLang(lang) {
    const next = normalizeLang(lang) || 'fr';
    localStorage.setItem(STORAGE_KEY, next);
    apply(document);
    window.dispatchEvent(new CustomEvent('daleel:languagechange', { detail: { lang: next } }));
  }

  function languageName(lang = getLang()) {
    return t(`lang.${lang}`);
  }

  function closeLanguageMenus(except = null) {
    document.querySelectorAll('.language-switcher.open').forEach((switcher) => {
      if (switcher === except) return;
      switcher.classList.remove('open');
      switcher.querySelector('.lang-trigger')?.setAttribute('aria-expanded', 'false');
    });
  }

  let menuListenersBound = false;

  function ensureLanguageMenuListeners() {
    if (menuListenersBound) return;
    menuListenersBound = true;
    document.addEventListener('click', () => closeLanguageMenus());
    document.addEventListener('keydown', (event) => {
      if (event.key === 'Escape') closeLanguageMenus();
    });
  }

  function fallbackSwitcherHost() {
    let host = document.getElementById('daleel-language-fallback');
    if (!host) {
      host = document.createElement('div');
      host.id = 'daleel-language-fallback';
      document.body?.appendChild(host);
    }
    return host;
  }

  function updateLanguageSwitchers() {
    document.querySelectorAll('.language-switcher').forEach((switcher) => {
      const current = getLang();
      switcher.setAttribute('aria-label', t('lang.current', { language: languageName(current) }));
      const currentLabel = switcher.querySelector('.lang-current');
      if (currentLabel) currentLabel.textContent = languageName(current);
      const trigger = switcher.querySelector('.lang-trigger');
      if (trigger) trigger.setAttribute('aria-label', t('lang.current', { language: languageName(current) }));
      switcher.querySelectorAll('.lang-option').forEach((option) => {
        const active = option.dataset.lang === current;
        option.textContent = languageName(option.dataset.lang);
        option.classList.toggle('active', active);
        option.setAttribute('aria-pressed', String(active));
        option.setAttribute('aria-checked', String(active));
      });
    });
  }

  function mountLanguageSwitcher(target) {
    const foundHost = typeof target === 'string' ? document.querySelector(target) : target;
    const host = foundHost || fallbackSwitcherHost();
    if (!host || host.querySelector('.language-switcher')) return;

    const switcher = document.createElement('div');
    switcher.className = 'language-switcher';
    switcher.setAttribute('role', 'group');
    switcher.innerHTML = `
      <button type="button" class="lang-trigger" aria-haspopup="menu" aria-expanded="false">
        <span class="lang-icon" aria-hidden="true">
          <svg viewBox="0 0 24 24" focusable="false">
            <circle cx="12" cy="12" r="9"></circle>
            <path d="M3 12h18M12 3c2.5 2.7 3.8 5.7 3.8 9S14.5 18.3 12 21M12 3c-2.5 2.7-3.8 5.7-3.8 9S9.5 18.3 12 21"></path>
          </svg>
        </span>
        <span class="lang-current"></span>
      </button>
      <div class="lang-menu" role="menu">
        ${SUPPORTED.map((lang) => `
          <button type="button" class="lang-option" data-lang="${lang}" role="menuitemradio">
            ${dict[lang][`lang.${lang}`]}
          </button>
        `).join('')}
      </div>
    `;

    const trigger = switcher.querySelector('.lang-trigger');
    trigger?.addEventListener('click', (event) => {
      event.stopPropagation();
      const shouldOpen = !switcher.classList.contains('open');
      closeLanguageMenus(switcher);
      switcher.classList.toggle('open', shouldOpen);
      trigger.setAttribute('aria-expanded', String(shouldOpen));
    });

    switcher.addEventListener('click', (event) => event.stopPropagation());

    switcher.querySelectorAll('.lang-option').forEach((option) => {
      option.addEventListener('click', () => {
        setLang(option.dataset.lang);
        closeLanguageMenus();
      });
    });

    host.appendChild(switcher);
    ensureLanguageMenuListeners();
    updateLanguageSwitchers();
  }

  function injectStyles() {
    if (document.getElementById('daleel-i18n-style')) return;
    const style = document.createElement('style');
    style.id = 'daleel-i18n-style';
    style.textContent = `
      #daleel-language-fallback{position:fixed;top:16px;right:16px;z-index:1000}
      .language-switcher{position:relative;display:inline-flex;align-items:center;z-index:30}
      .lang-trigger{height:34px;border:1px solid var(--border,#2a2a40);border-radius:10px;background:var(--bg-tertiary,var(--bg3,#1a1a2e));color:var(--text-primary,var(--text,#e8e6f0));padding:0 10px;display:inline-flex;align-items:center;gap:7px;cursor:pointer;font:inherit;font-size:12px;font-weight:700;white-space:nowrap;transition:.15s}
      .lang-trigger:hover,.language-switcher.open .lang-trigger{border-color:var(--border-accent,rgba(124,92,252,.3));background:var(--accent-glow,rgba(124,92,252,.15));color:var(--accent-light,var(--accent2,#a78bfa))}
      .lang-icon{display:inline-flex;align-items:center;justify-content:center;width:16px;height:16px;color:currentColor}
      .lang-icon svg{width:16px;height:16px;display:block;fill:none;stroke:currentColor;stroke-width:1.8;stroke-linecap:round;stroke-linejoin:round}
      .lang-menu{position:absolute;top:calc(100% + 8px);right:0;min-width:156px;padding:6px;border:1px solid var(--border,#2a2a40);border-radius:10px;background:var(--bg-card,var(--bg2,#16162a));box-shadow:0 12px 30px rgba(0,0,0,.32);display:none}
      .language-switcher.open .lang-menu{display:grid;gap:4px}
      .lang-option{height:34px;width:100%;border:0;background:transparent;color:var(--text-secondary,var(--text2,#9896a8));border-radius:8px;padding:0 10px;display:flex;align-items:center;justify-content:flex-start;cursor:pointer;font:inherit;font-size:13px;font-weight:700;white-space:nowrap;transition:.15s;text-align:left}
      .lang-option:hover,.lang-option.active{background:var(--accent-glow,rgba(124,92,252,.15));color:var(--accent-light,var(--accent2,#a78bfa))}
      html[dir="rtl"] #daleel-language-fallback{right:auto;left:16px}
      html[dir="rtl"] .lang-menu{right:auto;left:0}
      html[dir="rtl"] .lang-option{justify-content:flex-end;text-align:right}
      html[dir="rtl"] .header-info,html[dir="rtl"] .topbar-title,html[dir="rtl"] .section-title,html[dir="rtl"] .panel-title{text-align:right}
      html[dir="rtl"] th,html[dir="rtl"] td{text-align:right}
    `;
    document.head.appendChild(style);
  }

  function init(options = {}) {
    rebuildPhraseIndex();
    injectStyles();
    apply(document);

    if (options.switcher) {
      mountLanguageSwitcher(options.switcher);
    }

    if (typeof options.onChange === 'function') {
      window.addEventListener('daleel:languagechange', options.onChange);
    }
    const observer = new MutationObserver((mutations) => {
      if (isApplying) return;
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (node.nodeType === Node.ELEMENT_NODE) apply(node);
        });
      });
    });
    if (document.body) observer.observe(document.body, { childList: true, subtree: true });

    return getLang();
  }

  return {
    init,
    t,
    getLang,
    setLang,
    apply,
    mountLanguageSwitcher,
    isRtl: () => RTL.has(getLang()),
  };
})();

if (typeof window !== 'undefined') {
  window.DaleelI18n = DaleelI18n;
}
