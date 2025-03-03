import base64
import logging
import zipfile
from io import BytesIO
import xml.etree.ElementTree as ET
from datetime import datetime
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class IrSalaryDeclaration(models.Model):
    """Traitements et Salaires Declaration (Simpl-IR)"""
    _name = 'ir.salary.declaration'
    _description = 'Traitements et Salaires Declaration'
    _inherit = 'moroccan.edi.declaration'
    
    # Additional fields specific to IR declarations
    exercice_fiscal_du = fields.Date('From', required=True)
    exercice_fiscal_au = fields.Date('To', required=True)
    raison_sociale = fields.Char('Company Name', related='company_id.name')
    
    # Address information
    commune_id = fields.Many2one('dgi.commune', string='Commune')
    commune_code = fields.Char(related='commune_id.code')
    address = fields.Char('Address')
    
    # Various identification numbers
    numero_rc = fields.Char('RC Number')
    numero_cnss = fields.Char('CNSS Number')
    numero_ice = fields.Char('ICE Number')
    numero_tp = fields.Char('TP Number')
    numero_telephone = fields.Char('Phone Number')
    numero_fax = fields.Char('Fax Number')
    email = fields.Char('Email')
    
    # Statistics
    effectif_total = fields.Integer('Total Employees')
    nbr_perso_permanent = fields.Integer('Permanent Employees')
    nbr_perso_occasionnel = fields.Integer('Occasional Employees')
    nbr_stagiaires = fields.Integer('Interns')
    
    # Employee lists for different categories
    permanent_employee_ids = fields.One2many('ir.salary.declaration.permanent', 'declaration_id', string='Permanent Employees')
    occasional_employee_ids = fields.One2many('ir.salary.declaration.occasional', 'declaration_id', string='Occasional Employees')
    intern_ids = fields.One2many('ir.salary.declaration.intern', 'declaration_id', string='Interns')
    doctoral_ids = fields.One2many('ir.salary.declaration.doctoral', 'declaration_id', string='Doctoral Students')
    beneficiary_ids = fields.One2many('ir.salary.declaration.beneficiary', 'declaration_id', string='Beneficiaries')
    plan_beneficiary_ids = fields.One2many('ir.salary.declaration.plan', 'declaration_id', string='Plan Beneficiaries')
    exonerated_employee_ids = fields.One2many('ir.salary.declaration.exonerated', 'declaration_id', string='Exonerated Employees')
    exonerated_5725_employee_ids = fields.One2many('ir.salary.declaration.exonerated.5725', 'declaration_id', string='Exonerated 5725 Employees')
    
    # Totals
    total_mt_revenu_brut_imposable_pp = fields.Float('Total Gross Taxable Income PP')
    total_mt_revenu_net_imposable_pp = fields.Float('Total Net Taxable Income PP')
    total_mt_total_deduction_pp = fields.Float('Total Deductions PP')
    total_mt_ir_preleve_pp = fields.Float('Total IR Withheld PP')
    
    @api.model
    def create(self, vals):
        vals['declaration_type'] = 'ir'
        return super(IrSalaryDeclaration, self).create(vals)
    
    def action_generate_xml(self):
        """Generate XML file according to DGI specifications for Simpl-IR"""
        self.ensure_one()
        
        # Create root element
        root = ET.Element("TraitementEtSalaire")
        
        # Add header information
        ET.SubElement(root, "identifiantFiscal").text = self.company_id.vat
        
        # Handle company name (either name or raison_sociale)
        if self.company_id.is_company:
            ET.SubElement(root, "nom").text = ""
            ET.SubElement(root, "prenom").text = ""
            ET.SubElement(root, "raisonSociale").text = self.raison_sociale
        else:
            ET.SubElement(root, "nom").text = self.company_id.name.split(' ', 1)[0] if ' ' in self.company_id.name else self.company_id.name
            ET.SubElement(root, "prenom").text = self.company_id.name.split(' ', 1)[1] if ' ' in self.company_id.name else ""
            ET.SubElement(root, "raisonSociale").text = ""
        
        # Fiscal period
        ET.SubElement(root, "exerciceFiscalDu").text = self.exercice_fiscal_du.strftime('%Y-%m-%d')
        ET.SubElement(root, "exerciceFiscalAu").text = self.exercice_fiscal_au.strftime('%Y-%m-%d')
        ET.SubElement(root, "annee").text = self.year
        
        # Company information
        commune = ET.SubElement(root, "commune")
        ET.SubElement(commune, "code").text = self.commune_code or ""
        
        ET.SubElement(root, "adresse").text = self.address or ""
        ET.SubElement(root, "numeroCIN").text = ""  # Not applicable for companies
        ET.SubElement(root, "numeroCNSS").text = self.numero_cnss or ""
        ET.SubElement(root, "numeroCE").text = self.numero_ice or ""
        ET.SubElement(root, "numeroRC").text = self.numero_rc or ""
        ET.SubElement(root, "identifiantTP").text = self.numero_tp or ""
        ET.SubElement(root, "numeroFax").text = self.numero_fax or ""
        ET.SubElement(root, "numeroTelephone").text = self.numero_telephone or ""
        ET.SubElement(root, "email").text = self.email or ""
        
        # Statistics
        ET.SubElement(root, "effectifTotal").text = str(self.effectif_total or 0)
        ET.SubElement(root, "nbrPersoPermanent").text = str(self.nbr_perso_permanent or 0)
        ET.SubElement(root, "nbrPersoOccasionnel").text = str(self.nbr_perso_occasionnel or 0)
        ET.SubElement(root, "nbrStagiaires").text = str(self.nbr_stagiaires or 0)
        
        # Add totals
        ET.SubElement(root, "totalMtRevenuBrutImposablePP").text = f"{self.total_mt_revenu_brut_imposable_pp:.2f}"
        ET.SubElement(root, "totalMtRevenuNetImposablePP").text = f"{self.total_mt_revenu_net_imposable_pp:.2f}"
        ET.SubElement(root, "totalMtTotalDeductionPP").text = f"{self.total_mt_total_deduction_pp:.2f}"
        ET.SubElement(root, "totalMtIrPrelevePP").text = f"{self.total_mt_ir_preleve_pp:.2f}"
        
        # Add employee lists
        self._add_permanent_employees(root)
        self._add_occasional_employees(root)
        self._add_interns(root)
        self._add_doctoral_students(root)
        self._add_beneficiaries(root)
        self._add_plan_beneficiaries(root)
        self._add_exonerated_employees(root)
        self._add_exonerated_5725_employees(root)
        
        # Convert XML to string
        xml_string = ET.tostring(root, encoding='utf-8', method='xml')
        
        # Add XML declaration
        xml_string = b'<?xml version="1.0" encoding="UTF-8"?>' + xml_string
        
        # Store XML file
        self.xml_file = base64.b64encode(xml_string)
        self.xml_filename = f"Traitement_Salaire_{self.year}.xml"
        
        # Create ZIP file (not required by DGI for IR, but we keep the same structure)
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.writestr(self.xml_filename, xml_string)
        
        # Store ZIP file
        self.zip_file = base64.b64encode(zip_buffer.getvalue())
        self.zip_filename = f"Traitement_Salaire_{self.year}.zip"
        
        self.state = 'generated'
        return True
    
    def _add_permanent_employees(self, root):
        """Add permanent employees to XML"""
        if not self.permanent_employee_ids:
            return
        
        list_element = ET.SubElement(root, "listPersonnelPermanent")
        
        for employee in self.permanent_employee_ids:
            employee_element = ET.SubElement(list_element, "PersonnelPermanent")
            
            ET.SubElement(employee_element, "nom").text = employee.name or ""
            ET.SubElement(employee_element, "prenom").text = employee.first_name or ""
            ET.SubElement(employee_element, "adressePersonnelle").text = employee.address or ""
            ET.SubElement(employee_element, "numCNI").text = employee.cin or ""
            ET.SubElement(employee_element, "numCE").text = employee.ice or ""
            ET.SubElement(employee_element, "numPPR").text = employee.ppr or ""
            ET.SubElement(employee_element, "numCNSS").text = employee.cnss or ""
            ET.SubElement(employee_element, "ifu").text = employee.ifu or ""
            
            # Salary information
            ET.SubElement(employee_element, "salaireBaseAnnuel").text = f"{employee.base_salary:.2f}"
            ET.SubElement(employee_element, "mtBrutTraitementSalaire").text = f"{employee.gross_salary:.2f}"
            ET.SubElement(employee_element, "periode").text = str(employee.period or 0)
            ET.SubElement(employee_element, "mtExonere").text = f"{employee.exempt_amount:.2f}"
            ET.SubElement(employee_element, "mtEcheances").text = f"{employee.installments:.2f}"
            ET.SubElement(employee_element, "nbrReductions").text = str(employee.reductions_count or 0)
            ET.SubElement(employee_element, "mtIndemnite").text = f"{employee.indemnity_amount:.2f}"
            ET.SubElement(employee_element, "mtAvantages").text = f"{employee.benefits_amount:.2f}"
            ET.SubElement(employee_element, "mtRevenuBrutImposable").text = f"{employee.gross_taxable_income:.2f}"
            ET.SubElement(employee_element, "mtFraisProfess").text = f"{employee.professional_expenses:.2f}"
            ET.SubElement(employee_element, "mtCotisationAssur").text = f"{employee.insurance_contribution:.2f}"
            ET.SubElement(employee_element, "mtAutresRetenues").text = f"{employee.other_deductions:.2f}"
            ET.SubElement(employee_element, "mtRevenuNetImposable").text = f"{employee.net_taxable_income:.2f}"
            ET.SubElement(employee_element, "mtTotalDeduction").text = f"{employee.total_deduction:.2f}"
            ET.SubElement(employee_element, "irPreleve").text = f"{employee.ir_withheld:.2f}"
            
            # Additional flags and references
            ET.SubElement(employee_element, "casSportif").text = "true" if employee.is_sports_personnel else "false"
            ET.SubElement(employee_element, "numMatricule").text = employee.registration_number or ""
            if employee.permit_date:
                ET.SubElement(employee_element, "datePermis").text = employee.permit_date.strftime('%Y-%m-%d')
            if employee.authorization_date:
                ET.SubElement(employee_element, "dateAutorisation").text = employee.authorization_date.strftime('%Y-%m-%d')
            
            # Family situation
            family_situation = ET.SubElement(employee_element, "refSituationFamiliale")
            ET.SubElement(family_situation, "code").text = employee.family_situation or "C"  # Default to "Célibataire"
            
            # Tax rate reference
            tax_rate = ET.SubElement(employee_element, "refTaux")
            ET.SubElement(tax_rate, "code").text = employee.tax_rate_code or ""
            
            # Exempt elements if any
            if employee.exempt_element_ids:
                exempt_list = ET.SubElement(employee_element, "listElementsExonere")
                
                for exempt in employee.exempt_element_ids:
                    exempt_element = ET.SubElement(exempt_list, "ElementExonerePP")
                    ET.SubElement(exempt_element, "montantExonere").text = f"{exempt.amount:.2f}"
                    nature = ET.SubElement(exempt_element, "refNatureElementExonere")
                    ET.SubElement(nature, "code").text = exempt.nature_code
    
    def _add_occasional_employees(self, root):
        """Add occasional employees to XML"""
        if not self.occasional_employee_ids:
            return
        
        list_element = ET.SubElement(root, "listPersonnelOccasionnel")
        
        for employee in self.occasional_employee_ids:
            employee_element = ET.SubElement(list_element, "PersonnelOccasionnel")
            
            ET.SubElement(employee_element, "nom").text = employee.name or ""
            ET.SubElement(employee_element, "prenom").text = employee.first_name or ""
            ET.SubElement(employee_element, "adressePersonnelle").text = employee.address or ""
            ET.SubElement(employee_element, "numCNI").text = employee.cin or ""
            ET.SubElement(employee_element, "numCE").text = employee.ice or ""
            ET.SubElement(employee_element, "ifu").text = employee.ifu or ""
            
            # Salary information
            ET.SubElement(employee_element, "mtBrutSommes").text = f"{employee.gross_amount:.2f}"
            ET.SubElement(employee_element, "irPreleve").text = f"{employee.ir_withheld:.2f}"
            ET.SubElement(employee_element, "profession").text = employee.profession or ""
    
    def _add_interns(self, root):
        """Add interns to XML"""
        if not self.intern_ids:
            return
        
        list_element = ET.SubElement(root, "listStagiaires")
        
        for intern in self.intern_ids:
            intern_element = ET.SubElement(list_element, "Stagiaire")
            
            ET.SubElement(intern_element, "nom").text = intern.name or ""
            ET.SubElement(intern_element, "prenom").text = intern.first_name or ""
            ET.SubElement(intern_element, "adressePersonnelle").text = intern.address or ""
            ET.SubElement(intern_element, "numCNI").text = intern.cin or ""
            ET.SubElement(intern_element, "numCE").text = intern.ice or ""
            ET.SubElement(intern_element, "numCNSS").text = intern.cnss or ""
            ET.SubElement(intern_element, "ifu").text = intern.ifu or ""
            
            # Internship information
            ET.SubElement(intern_element, "mtBrutTraitementSalaire").text = f"{intern.gross_salary:.2f}"
            ET.SubElement(intern_element, "mtBrutIndemnites").text = f"{intern.gross_indemnities:.2f}"
            ET.SubElement(intern_element, "mtRetenues").text = f"{intern.deductions:.2f}"
            ET.SubElement(intern_element, "mtRevenuNetImposable").text = f"{intern.net_taxable_income:.2f}"
            ET.SubElement(intern_element, "periode").text = str(intern.period or 0)
    
    def _add_doctoral_students(self, root):
        """Add doctoral students to XML"""
        if not self.doctoral_ids:
            return
        
        list_element = ET.SubElement(root, "listDoctorants")
        
        for doctoral in self.doctoral_ids:
            doctoral_element = ET.SubElement(list_element, "Doctorant")
            
            ET.SubElement(doctoral_element, "nom").text = doctoral.name or ""
            ET.SubElement(doctoral_element, "prenom").text = doctoral.first_name or ""
            ET.SubElement(doctoral_element, "adressePersonnelle").text = doctoral.address or ""
            ET.SubElement(doctoral_element, "numCNI").text = doctoral.cin or ""
            ET.SubElement(doctoral_element, "numCE").text = doctoral.ice or ""
            
            # Doctoral student information
            ET.SubElement(doctoral_element, "mtBrutIndemnites").text = f"{doctoral.gross_indemnities:.2f}"
    
    def _add_beneficiaries(self, root):
        """Add beneficiaries to XML"""
        if not self.beneficiary_ids:
            return
        
        list_element = ET.SubElement(root, "listBeneficiaires")
        
        for beneficiary in self.beneficiary_ids:
            beneficiary_element = ET.SubElement(list_element, "Beneficiaire")
            
            ET.SubElement(beneficiary_element, "nom").text = beneficiary.name or ""
            ET.SubElement(beneficiary_element, "prenom").text = beneficiary.first_name or ""
            ET.SubElement(beneficiary_element, "adressePersonnelle").text = beneficiary.address or ""
            ET.SubElement(beneficiary_element, "numCNI").text = beneficiary.cin or ""
            ET.SubElement(beneficiary_element, "numCE").text = beneficiary.ice or ""
            ET.SubElement(beneficiary_element, "numCNSS").text = beneficiary.cnss or ""
            ET.SubElement(beneficiary_element, "ifu").text = beneficiary.ifu or ""
            
            # Stock options information
            ET.SubElement(beneficiary_element, "organisme").text = beneficiary.organization or ""
            ET.SubElement(beneficiary_element, "nbrActionsAcquises").text = str(beneficiary.acquired_shares or 0)
            ET.SubElement(beneficiary_element, "nbrActionsDistribuees").text = str(beneficiary.distributed_shares or 0)
            ET.SubElement(beneficiary_element, "prixAcquisition").text = f"{beneficiary.acquisition_price:.2f}"
            ET.SubElement(beneficiary_element, "valeurActionAttribution").text = f"{beneficiary.share_allocation_value:.2f}"
            ET.SubElement(beneficiary_element, "valeurActionLeveeOption").text = f"{beneficiary.share_option_value:.2f}"
            ET.SubElement(beneficiary_element, "mtAbondement").text = f"{beneficiary.subsidy_amount:.2f}"
            ET.SubElement(beneficiary_element, "nbrActionsCedees").text = str(beneficiary.sold_shares or 0)
            ET.SubElement(beneficiary_element, "complementSalaire").text = f"{beneficiary.salary_supplement:.2f}"
            
            # Dates
            if beneficiary.attribution_date:
                ET.SubElement(beneficiary_element, "dateAttribution").text = beneficiary.attribution_date.strftime('%Y-%m-%d')
            if beneficiary.option_exercise_date:
                ET.SubElement(beneficiary_element, "dateLeveOption").text = beneficiary.option_exercise_date.strftime('%Y-%m-%d')
            if beneficiary.transfer_date:
                ET.SubElement(beneficiary_element, "dateCession").text = beneficiary.transfer_date.strftime('%Y-%m-%d')
    
    def _add_plan_beneficiaries(self, root):
        """Add savings plan beneficiaries to XML"""
        if not self.plan_beneficiary_ids:
            return
        
        list_element = ET.SubElement(root, "listBeneficiairesPlanEpargne")
        
        for beneficiary in self.plan_beneficiary_ids:
            beneficiary_element = ET.SubElement(list_element, "BeneficiairePlanEpargne")
            
            ET.SubElement(beneficiary_element, "nom").text = beneficiary.name or ""
            ET.SubElement(beneficiary_element, "prenom").text = beneficiary.first_name or ""
            ET.SubElement(beneficiary_element, "adressePersonnelle").text = beneficiary.address or ""
            ET.SubElement(beneficiary_element, "numCNI").text = beneficiary.cin or ""
            ET.SubElement(beneficiary_element, "numCE").text = beneficiary.ice or ""
            
            # Commune information
            commune = ET.SubElement(beneficiary_element, "commune")
            ET.SubElement(commune, "code").text = beneficiary.commune_code or ""
            
            # Plan information
            ET.SubElement(beneficiary_element, "numPlan").text = beneficiary.plan_number or ""
            ET.SubElement(beneficiary_element, "duree").text = str(beneficiary.duration or 0)
            
            if beneficiary.opening_date:
                ET.SubElement(beneficiary_element, "dateOuverture").text = beneficiary.opening_date.strftime('%Y-%m-%d')
            
            ET.SubElement(beneficiary_element, "mtAbondement").text = f"{beneficiary.subsidy_amount:.2f}"
            ET.SubElement(beneficiary_element, "mtAnuuelRevenuSalarial").text = f"{beneficiary.annual_salary_income:.2f}"
    
    def _add_exonerated_employees(self, root):
        """Add exonerated employees to XML"""
        if not self.exonerated_employee_ids:
            return
        
        list_element = ET.SubElement(root, "listPersonnelExonere")
        
        for employee in self.exonerated_employee_ids:
            employee_element = ET.SubElement(list_element, "PersonnelExonere")
            
            ET.SubElement(employee_element, "nom").text = employee.name or ""
            ET.SubElement(employee_element, "prenom").text = employee.first_name or ""
            ET.SubElement(employee_element, "adressePersonnelle").text = employee.address or ""
            ET.SubElement(employee_element, "numCNI").text = employee.cin or ""
            ET.SubElement(employee_element, "numCE").text = employee.ice or ""
            ET.SubElement(employee_element, "numCNSS").text = employee.cnss or ""
            ET.SubElement(employee_element, "ifu").text = employee.ifu or ""
            
            ET.SubElement(employee_element, "periode").text = str(employee.period or 0)
            
            if employee.recruitment_date:
                ET.SubElement(employee_element, "dateRecrutement").text = employee.recruitment_date.strftime('%Y-%m-%d')
            
            # Salary information
            ET.SubElement(employee_element, "mtBrutTraitementSalaire").text = f"{employee.gross_salary:.2f}"
            ET.SubElement(employee_element, "mtIndemniteArgentNature").text = f"{employee.money_benefits:.2f}"
            ET.SubElement(employee_element, "mtIndemniteFraisPro").text = f"{employee.professional_expenses:.2f}"
            ET.SubElement(employee_element, "mtRevenuBrutImposable").text = f"{employee.gross_taxable_income:.2f}"
            ET.SubElement(employee_element, "mtRetenuesOperees").text = f"{employee.deductions:.2f}"
            ET.SubElement(employee_element, "mtRevenuNetImposable").text = f"{employee.net_taxable_income:.2f}"
    
    def _add_exonerated_5725_employees(self, root):
        """Add exonerated 5725 employees to XML (Article 247 and 247 bis)"""
        if not self.exonerated_5725_employee_ids:
            return
        
        list_element = ET.SubElement(root, "listPersonnelExonere5725")
        
        for employee in self.exonerated_5725_employee_ids:
            employee_element = ET.SubElement(list_element, "PersonnelExonere5725")
            
            ET.SubElement(employee_element, "nom").text = employee.name or ""
            ET.SubElement(employee_element, "prenom").text = employee.first_name or ""
            ET.SubElement(employee_element, "adressePersonnelle").text = employee.address or ""
            ET.SubElement(employee_element, "numCNI").text = employee.cin or ""
            ET.SubElement(employee_element, "numCE").text = employee.ice or ""
            ET.SubElement(employee_element, "numCNSS").text = employee.cnss or ""
            ET.SubElement(employee_element, "ifu").text = employee.ifu or ""
            
            # Specific dates for Article 247 and 247 bis
            if employee.recruitment_date:
                ET.SubElement(employee_element, "dateRecrutement").text = employee.recruitment_date.strftime('%Y-%m-%d')
            if employee.birth_date:
                ET.SubElement(employee_element, "dateNaissance").text = employee.birth_date.strftime('%Y-%m-%d')
            if employee.employment_loss_date:
                ET.SubElement(employee_element, "datePerteEmploi").text = employee.employment_loss_date.strftime('%Y-%m-%d')
            
            # Salary information
            ET.SubElement(employee_element, "mtBrutTraitementSalaire").text = f"{employee.gross_salary:.2f}"
            ET.SubElement(employee_element, "mtIndemniteArgentNature").text = f"{employee.money_benefits:.2f}"
            ET.SubElement(employee_element, "periode").text = str(employee.period or 0)
            ET.SubElement(employee_element, "mtIndemniteFraisPro").text = f"{employee.professional_expenses:.2f}"
            ET.SubElement(employee_element, "mtRevenuBrutImposable").text = f"{employee.gross_taxable_income:.2f}"
            ET.SubElement(employee_element, "mtRetenuesOperees").text = f"{employee.deductions:.2f}"
            ET.SubElement(employee_element, "mtRevenuNetImposable").text = f"{employee.net_taxable_income:.2f}"
    
    def _prepare_api_data(self):
        """Prepare data for IR API call"""
        return {
            'identifiantFiscal': self.company_id.vat,
            'annee': self.year,
            'exercice_fiscal_du': self.exercice_fiscal_du.strftime('%Y-%m-%d'),
            'exercice_fiscal_au': self.exercice_fiscal_au.strftime('%Y-%m-%d'),
            'declaration_type': 'ir_traitement_salaire'
        }


# Employee data models

class IrSalaryDeclarationPermanent(models.Model):
    """Permanent Employee for IR Salary Declaration"""
    _name = 'ir.salary.declaration.permanent'
    _description = 'Permanent Employee for Salary Declaration'
    
    declaration_id = fields.Many2one('ir.salary.declaration', string='Declaration', required=True, ondelete='cascade')
    name = fields.Char('Last Name', required=True)
    first_name = fields.Char('First Name', required=True)
    address = fields.Char('Address')
    cin = fields.Char('CIN Number')
    ice = fields.Char('ICE Number')
    ppr = fields.Char('PPR Number')
    cnss = fields.Char('CNSS Number')
    ifu = fields.Char('IFU Number')
    
    # Salary information
    base_salary = fields.Float('Base Annual Salary')
    gross_salary = fields.Float('Gross Salary')
    period = fields.Integer('Period')
    exempt_amount = fields.Float('Exempt Amount')
    installments = fields.Float('Installments')
    reductions_count = fields.Integer('Number of Reductions')
    indemnity_amount = fields.Float('Indemnity Amount')
    benefits_amount = fields.Float('Benefits Amount')
    gross_taxable_income = fields.Float('Gross Taxable Income')
    professional_expenses = fields.Float('Professional Expenses')
    insurance_contribution = fields.Float('Insurance Contribution')
    other_deductions = fields.Float('Other Deductions')
    net_taxable_income = fields.Float('Net Taxable Income', compute='_compute_net_taxable_income', store=True)
    total_deduction = fields.Float('Total Deduction', compute='_compute_total_deduction', store=True)
    ir_withheld = fields.Float('IR Withheld')
    
    # Additional flags and references
    is_sports_personnel = fields.Boolean('Sports Personnel')
    registration_number = fields.Char('Registration Number')
    permit_date = fields.Date('Permit Date')
    authorization_date = fields.Date('Authorization Date')
    
    # Family situation and tax rate
    family_situation = fields.Selection([
        ('C', 'Single'),
        ('M', 'Married'),
        ('D', 'Divorced'),
        ('V', 'Widowed')
    ], string='Family Situation', default='C')
    tax_rate_code = fields.Char('Tax Rate Code')
    
    # Exempt elements
    exempt_element_ids = fields.One2many('ir.salary.declaration.exempt.element', 'employee_id', string='Exempt Elements')
    
    @api.depends('gross_taxable_income', 'professional_expenses', 'insurance_contribution', 'other_deductions')
    def _compute_total_deduction(self):
        for record in self:
            record.total_deduction = record.professional_expenses + record.insurance_contribution + record.other_deductions
    
    @api.depends('gross_taxable_income', 'total_deduction')
    def _compute_net_taxable_income(self):
        for record in self:
            record.net_taxable_income = record.gross_taxable_income - record.total_deduction


class IrSalaryDeclarationExemptElement(models.Model):
    """Exempt Element for IR Salary Declaration"""
    _name = 'ir.salary.declaration.exempt.element'
    _description = 'Exempt Element for Salary Declaration'
    
    employee_id = fields.Many2one('ir.salary.declaration.permanent', string='Employee', required=True, ondelete='cascade')
    amount = fields.Float('Exempt Amount', required=True)
    nature_code = fields.Char('Nature Code', required=True)
    nature_description = fields.Char('Nature Description')


class IrSalaryDeclarationOccasional(models.Model):
    """Occasional Employee for IR Salary Declaration"""
    _name = 'ir.salary.declaration.occasional'
    _description = 'Occasional Employee for Salary Declaration'
    
    declaration_id = fields.Many2one('ir.salary.declaration', string='Declaration', required=True, ondelete='cascade')
    name = fields.Char('Last Name', required=True)
    first_name = fields.Char('First Name', required=True)
    address = fields.Char('Address')
    cin = fields.Char('CIN Number')
    ice = fields.Char('ICE Number')
    ifu = fields.Char('IFU Number')
    
    # Work information
    gross_amount = fields.Float('Gross Amount')
    ir_withheld = fields.Float('IR Withheld')
    profession = fields.Char('Profession')


class IrSalaryDeclarationIntern(models.Model):
    """Intern for IR Salary Declaration"""
    _name = 'ir.salary.declaration.intern'
    _description = 'Intern for Salary Declaration'
    
    declaration_id = fields.Many2one('ir.salary.declaration', string='Declaration', required=True, ondelete='cascade')
    name = fields.Char('Last Name', required=True)
    first_name = fields.Char('First Name', required=True)
    address = fields.Char('Address')
    cin = fields.Char('CIN Number')
    ice = fields.Char('ICE Number')
    cnss = fields.Char('CNSS Number')
    ifu = fields.Char('IFU Number')
    
    # Internship information
    gross_salary = fields.Float('Gross Salary')
    gross_indemnities = fields.Float('Gross Indemnities')
    deductions = fields.Float('Deductions')
    net_taxable_income = fields.Float('Net Taxable Income')
    period = fields.Integer('Period')


class IrSalaryDeclarationDoctoral(models.Model):
    """Doctoral Student for IR Salary Declaration"""
    _name = 'ir.salary.declaration.doctoral'
    _description = 'Doctoral Student for Salary Declaration'
    
    declaration_id = fields.Many2one('ir.salary.declaration', string='Declaration', required=True, ondelete='cascade')
    name = fields.Char('Last Name', required=True)
    first_name = fields.Char('First Name', required=True)
    address = fields.Char('Address')
    cin = fields.Char('CIN Number')
    ice = fields.Char('ICE Number')
    
    gross_indemnities = fields.Float('Gross Indemnities')


class IrSalaryDeclarationBeneficiary(models.Model):
    """Stock Options Beneficiary for IR Salary Declaration"""
    _name = 'ir.salary.declaration.beneficiary'
    _description = 'Stock Options Beneficiary for Salary Declaration'
    
    declaration_id = fields.Many2one('ir.salary.declaration', string='Declaration', required=True, ondelete='cascade')
    name = fields.Char('Last Name', required=True)
    first_name = fields.Char('First Name', required=True)
    address = fields.Char('Address')
    cin = fields.Char('CIN Number')
    ice = fields.Char('ICE Number')
    cnss = fields.Char('CNSS Number')
    ifu = fields.Char('IFU Number')
    
    # Stock options information
    organization = fields.Char('Organization')
    acquired_shares = fields.Integer('Acquired Shares')
    distributed_shares = fields.Integer('Distributed Shares')
    acquisition_price = fields.Float('Acquisition Price')
    share_allocation_value = fields.Float('Share Allocation Value')
    share_option_value = fields.Float('Share Option Value')
    subsidy_amount = fields.Float('Subsidy Amount')
    sold_shares = fields.Integer('Sold Shares')
    salary_supplement = fields.Float('Salary Supplement')
    
    # Dates
    attribution_date = fields.Date('Attribution Date')
    option_exercise_date = fields.Date('Option Exercise Date')
    transfer_date = fields.Date('Transfer Date')


class IrSalaryDeclarationPlan(models.Model):
    """Savings Plan Beneficiary for IR Salary Declaration"""
    _name = 'ir.salary.declaration.plan'
    _description = 'Savings Plan Beneficiary for Salary Declaration'
    
    declaration_id = fields.Many2one('ir.salary.declaration', string='Declaration', required=True, ondelete='cascade')
    name = fields.Char('Last Name', required=True)
    first_name = fields.Char('First Name', required=True)
    address = fields.Char('Address')
    cin = fields.Char('CIN Number')
    ice = fields.Char('ICE Number')
    
    # Commune
    commune_id = fields.Many2one('dgi.commune', string='Commune')
    commune_code = fields.Char(related='commune_id.code')
    
    # Plan information
    plan_number = fields.Char('Plan Number')
    duration = fields.Integer('Duration')
    opening_date = fields.Date('Opening Date')
    subsidy_amount = fields.Float('Subsidy Amount')
    annual_salary_income = fields.Float('Annual Salary Income')


class IrSalaryDeclarationExonerated(models.Model):
    """Exonerated Employee for IR Salary Declaration"""
    _name = 'ir.salary.declaration.exonerated'
    _description = 'Exonerated Employee for Salary Declaration'
    
    declaration_id = fields.Many2one('ir.salary.declaration', string='Declaration', required=True, ondelete='cascade')
    name = fields.Char('Last Name', required=True)
    first_name = fields.Char('First Name', required=True)
    address = fields.Char('Address')
    cin = fields.Char('CIN Number')
    ice = fields.Char('ICE Number')
    cnss = fields.Char('CNSS Number')
    ifu = fields.Char('IFU Number')
    
    period = fields.Integer('Period')
    recruitment_date = fields.Date('Recruitment Date')
    
    # Salary information
    gross_salary = fields.Float('Gross Salary')
    money_benefits = fields.Float('Money Benefits')
    professional_expenses = fields.Float('Professional Expenses')
    gross_taxable_income = fields.Float('Gross Taxable Income')
    deductions = fields.Float('Deductions')
    net_taxable_income = fields.Float('Net Taxable Income')


class IrSalaryDeclarationExonerated5725(models.Model):
    """Exonerated 5725 Employee for IR Salary Declaration (Article 247 and 247 bis)"""
    _name = 'ir.salary.declaration.exonerated.5725'
    _description = 'Exonerated 5725 Employee for Salary Declaration'
    
    declaration_id = fields.Many2one('ir.salary.declaration', string='Declaration', required=True, ondelete='cascade')
    name = fields.Char('Last Name', required=True)
    first_name = fields.Char('First Name', required=True)
    address = fields.Char('Address')
    cin = fields.Char('CIN Number')
    ice = fields.Char('ICE Number')
    cnss = fields.Char('CNSS Number')
    ifu = fields.Char('IFU Number')
    
    recruitment_date = fields.Date('Recruitment Date')
    birth_date = fields.Date('Birth Date')
    employment_loss_date = fields.Date('Employment Loss Date')
    
    # Salary information
    gross_salary = fields.Float('Gross Salary')
    money_benefits = fields.Float('Money Benefits')
    period = fields.Integer('Period')
    professional_expenses = fields.Float('Professional Expenses')
    gross_taxable_income = fields.Float('Gross Taxable Income')
    deductions = fields.Float('Deductions')
    net_taxable_income = fields.Float('Net Taxable Income')


class HrEmployee(models.Model):
    """Extend HR Employee to add fields for EDI declarations"""
    _inherit = 'hr.employee'
    
    cin = fields.Char('CIN Number')
    ice = fields.Char('ICE Number')
    ppr = fields.Char('PPR Number')
    cnss = fields.Char('CNSS Number')
    ifu = fields.Char('IFU Number')
    is_sports_personnel = fields.Boolean('Sports Personnel')
    
    # Add fields for 247 and 247 bis articles
    is_247_exempt = fields.Boolean('Exempt under Article 247')
    is_247bis_exempt = fields.Boolean('Exempt under Article 247 bis')
    employment_loss_date = fields.Date('Employment Loss Date')
